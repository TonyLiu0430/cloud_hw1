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
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

type MessageJson struct {
	Sender_uuid string `json:"sender_uuid"`
	Message     string `json:"message"`
}

type Message struct {
	Sender_uuid  string
	Reciver_uuid string
	Message      string
	Timestamp    time.Time
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

	req, err := http.NewRequest("GET", backend_url+"/internal/userId", nil)
	if err != nil {
		return "", err
	}

	for _, c := range cookies {
		req.AddCookie(c)
	}

	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}

	if resp.StatusCode != 200 {
		return "", err
	}

	userIdBytes, err := io.ReadAll(resp.Body)
	defer resp.Body.Close()
	if err != nil {
		return "", err
	}

	return string(userIdBytes), nil
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
	for range 10 {
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
	http.HandleFunc("/message", func(w http.ResponseWriter, r *http.Request) {
		c, err := websocket.Accept(w, r, nil)
		if err != nil {
			return
		}
		userId, err := get_userId(r)
		if err != nil {
			return
		}
		defer c.Close(websocket.StatusInternalError, "500 Internal Server Error")
		defer func() {
			clients.Delete(userId)
		}()
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
				Sender_uuid:  mj.Sender_uuid,
				Reciver_uuid: userId,
				Message:      mj.Message,
				Timestamp:    time.Now(),
			}
			if err := saveMsg(m); err != nil {
				fmt.Println("Error saving message:", err)
				return
			}
			msgs <- m
		}
		c.Close(websocket.StatusNormalClosure, "")
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

	http.ListenAndServe(":4350", nil)
}
