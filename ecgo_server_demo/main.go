package main

import (
	"encoding/binary"
	"fmt"
	"log"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
)

func main() {
	ecg_queue := NewEcgQueue(6000)

	client := createMqttClient()
	client.Subscribe("ecg", byte(0), func(c mqtt.Client, m mqtt.Message) {

		data := m.Payload()
		for i := 0; i < len(data)/2; i++ {
			uint_value := binary.BigEndian.Uint16(data[2*i : 2*i+2])
			// fmt.Println(uint_value)
			fmt.Println("len:", len(ecg_queue.items))
			ecg_queue.Enqueue(uint16(uint_value))
		}
	})

	for {
		ecg_queue.Plot()
		time.Sleep(500 * time.Millisecond)
	}
}

func createMqttClient() mqtt.Client {
	connectAddress := fmt.Sprintf("%s://%s:%d", "mqtt", "47.113.224.100", 1883)
	client_id := fmt.Sprintf("go-client-%d", 0)

	fmt.Println("connect address: ", connectAddress)
	opts := mqtt.NewClientOptions()
	opts.AddBroker(connectAddress)
	opts.SetClientID(client_id)
	opts.SetKeepAlive(time.Second * 60)
	client := mqtt.NewClient(opts)
	token := client.Connect()
	// if connection failed, exit
	if token.WaitTimeout(3*time.Second) && token.Error() != nil {
		log.Fatal(token.Error())
	}
	return client
}
