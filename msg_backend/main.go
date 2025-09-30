package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"sync"
	"time"

	"github.com/coder/websocket"
	"github.com/gin-gonic/gin"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

type MessageJson struct {
	Reciver_uuid string `json:"reciver_uuid"`
	Message      string `json:"message"`
}

type Message struct {
	Sender_uuid  string    `bson:"sender_uuid" json:"sender_uuid"`
	Reciver_uuid string    `bson:"reciver_uuid" json:"reciver_uuid"`
	Message      string    `bson:"message" json:"message"`
	Timestamp    time.Time `bson:"timestamp" json:"timestamp"`
}

type WebSockClient struct {
	c *websocket.Conn
	r *http.Request
}

var mongoClient *mongo.Client

func saveMsg(msg Message) error {
	collection := mongoClient.Database("chatdb").Collection("messages")
	_, err := collection.InsertOne(context.TODO(), msg)
	return err
}

func get_userId(r *http.Request) (string, error) {
	client := http.DefaultClient
	backend_url, ok := os.LookupEnv("BACKEND_URL")
	if !ok {
		backend_url = "backend"
	}
	cookies := r.Cookies()

	req, err := http.NewRequest("GET", backend_url+"/api/user_id", nil)
	if err != nil {
		return "", err
	}

	fmt.Println(backend_url + "/api/user_id")

	for _, c := range cookies {
		req.AddCookie(c)
	}

	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}

	if resp.StatusCode != 200 {
		return "", fmt.Errorf("status code not 200: %d", resp.StatusCode)
	}

	userIdBytes, err := io.ReadAll(resp.Body)
	defer resp.Body.Close()
	if err != nil {
		return "", err
	}

	return string(userIdBytes), nil
}

func getHistory(userId string, peerId string) ([]Message, error) {
	collection := mongoClient.Database("chatdb").Collection("messages")
	filter := bson.M{
		"$or": []bson.M{
			{"sender_uuid": userId, "reciver_uuid": peerId},
			{"sender_uuid": peerId, "reciver_uuid": userId},
		},
	}
	opts := options.Find().SetSort(bson.D{{Key: "timestamp", Value: 1}})
	cursor, err := collection.Find(context.TODO(), filter, opts)
	if err != nil {
		fmt.Println("Error fetching history:", err)
		return nil, err
	}
	defer cursor.Close(context.TODO())
	var history []Message
	if err := cursor.All(context.TODO(), &history); err != nil {
		fmt.Println("Error decoding history:", err)
		return nil, err
	}
	for _, msg := range history {
		fmt.Printf("History: %+v\n", msg)
	}
	fmt.Println("History length:", len(history))
	return history, nil
}

func main() {
	msgs := make(chan Message)
	clients := sync.Map{}
	// 感覺有問題 之後再改
	/**TODO**/
	mongodb_connect_string, ok := os.LookupEnv("MONGODB_CONNECTION_STRING")
	if !ok {
		panic("cannot get mongodb connection string in environ")
	}
	for range 20 {
		var err error
		mongoClient, err = mongo.Connect(context.TODO(), options.Client().ApplyURI(mongodb_connect_string))
		if err == nil {
			break
		}
		fmt.Println("MongoDB not ready retry")
		time.Sleep(2 * time.Second)
	}
	if mongoClient == nil {
		panic("failed to connect MongoDB")
	}

	r := gin.Default()

	// websocket message service
	mux := http.NewServeMux()
	mux.HandleFunc("/api/message/message", func(w http.ResponseWriter, r *http.Request) {
		// 姬芭 用 gin 會有 bug !!!
		userId, err := get_userId(r)
		if err != nil {
			http.Error(w, "Permission denied", http.StatusUnauthorized)
			return
		}
		fmt.Println("User", userId, "connected to websocket")
		c, err := websocket.Accept(w, r, &websocket.AcceptOptions{
			OriginPatterns: []string{"*"},
		})
		if err != nil {
			fmt.Println("Failed to accept websocket:", err)
			return
		}
		fmt.Println("WebSocket connection established for user:", userId)
		//c.Write(r.Context(), websocket.MessageText, []byte("connected to message server"))

		defer c.Close(websocket.StatusInternalError, "500 Internal Server Error")
		defer func() {
			clients.Delete(userId)
		}()
		_, peerId, err := c.Read(r.Context())
		if err != nil {
			return
		}
		fmt.Println("User", userId, "chat with", string(peerId))
		// 對話歷史紀錄
		history, err := getHistory(userId, string(peerId))
		if err != nil {
			fmt.Println("Error getting history:", err)
			return
		}
		if len(history) == 0 {
			c.Write(r.Context(), websocket.MessageText, []byte("[]"))
		} else {
			historyByte, err := json.Marshal(history)
			if err != nil {
				fmt.Println("Error marshalling history:", err)
				return
			}
			c.Write(r.Context(), websocket.MessageText, historyByte)
		}

		clients.Store(userId, WebSockClient{
			r: r,
			c: c,
		})
		for {
			_, msg, err := c.Read(r.Context())
			if err != nil {
				break
			}
			var mj MessageJson
			if err := json.Unmarshal(msg, &mj); err != nil {
				fmt.Println("Error unmarshalling message:", err)
				continue
			}
			m := Message{
				Sender_uuid:  userId,
				Reciver_uuid: mj.Reciver_uuid,
				Message:      mj.Message,
				Timestamp:    time.Now(),
			}
			if err := saveMsg(m); err != nil {
				fmt.Println("Error saving message:", err)
				return
			}
			msgs <- m

			//echo message
			var mByte []byte
			mByte, err = json.Marshal(m)
			if err != nil {
				fmt.Println("Error marshalling message:", err)
				continue
			}
			c.Write(r.Context(), websocket.MessageText, mByte)
		}
		c.Close(websocket.StatusNormalClosure, "")
	})

	// 拿到所有交談過的對象 order by last message time
	r.GET("/api/message/user_list", func(c *gin.Context) {
		userId, err := get_userId(c.Request)
		if err != nil {
			c.JSON(http.StatusForbidden, gin.H{
				"message": "Permission denied Not login",
			})
			return
		}
		collection := mongoClient.Database("chatdb").Collection("messages")

		pipeline := []bson.M{
			{"$match": bson.M{"$or": []bson.M{
				{"sender_uuid": userId},
				{"reciver_uuid": userId},
			}}},
			{"$project": bson.M{
				"peer": bson.M{"$cond": bson.A{
					bson.M{"$eq": bson.A{"$sender_uuid", userId}},
					"$reciver_uuid",
					"$sender_uuid",
				}},
				"timestamp": 1,
			}},
			{"$group": bson.M{
				"_id":               "$peer",
				"last_message_time": bson.M{"$max": "$timestamp"},
			}},
			{"$sort": bson.M{"last_message_time": -1}},
		}
		cursor, err := collection.Aggregate(context.TODO(), pipeline)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{
				"message": "Failed to query user list",
			})
			return
		}
		defer cursor.Close(context.TODO())
		var userList []bson.M
		if err = cursor.All(context.TODO(), &userList); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{
				"message": "Failed to parse user list",
			})
			return
		}
		c.JSON(http.StatusOK, gin.H{
			"user_list": userList,
		})
	})

	go func() {
		for {
			msg := <-msgs
			reciver := msg.Reciver_uuid
			clientAny, ok := clients.Load(reciver)
			if !ok {
				continue
			}
			client := clientAny.(WebSockClient)
			fmt.Println("message :", msg.Message, "from", msg.Sender_uuid, "to", reciver)
			msgByte, err := json.Marshal(msg) // 這裡能error那整個程式也不用跑了
			if err != nil {
				panic("json marshal failed abort")
			}
			err = client.c.Write(client.r.Context(), websocket.MessageText, msgByte)
			if err != nil {
				// websocket 可能已關閉 不管他
				continue
			}
		}
	}()

	mux.Handle("/", r)
	http.ListenAndServe(":4350", mux)
}
