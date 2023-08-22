use anyhow::{Result, bail};
use esp_idf_sys::{nvs_flash_init};
// use core::time::Duration;
use std::{sync::{Arc, Mutex}};
use std::str;

use esp_idf_hal::delay::FreeRtos;
use esp_idf_hal::peripherals::Peripherals;

use esp_idf_hal::adc::config::Config;
use esp_idf_hal::adc::Atten11dB;
use esp_idf_hal::adc::*;
use esp_idf_hal::gpio::Gpio4;

use wifi::wifi;
use esp_idf_svc::{eventloop::EspSystemEventLoop, mqtt::client::{EspMqttClient}};


use embedded_svc::mqtt::client::{Details::Complete, Event::Received, QoS};

use rgb_led::{RGB8, WS2812RMT};
fn main() -> Result<()> {
    esp_idf_sys::link_patches();
    let sysloop = EspSystemEventLoop::take()?;

    let peripherals = Peripherals::take().unwrap();
    
    let mut adc = AdcDriver::new(peripherals.adc1, &Config::new().calibration(true))?;
    let mut adc_pin: esp_idf_hal::adc::AdcChannelDriver<'_, Gpio4, Atten11dB<_>> =
        AdcChannelDriver::new(peripherals.pins.gpio4)?;
    
    let led = WS2812RMT::new(peripherals.pins.gpio48, peripherals.rmt.channel0)?;
    let led_rc = Arc::new(Mutex::new(led));

    unsafe {
        nvs_flash_init();
    }
    let _wifi = match wifi("PDCN","1234567890",peripherals.modem,sysloop) {
        Ok(inner) => inner, 
        Err(err) => {
            led_rc.clone().lock().unwrap().set_pixel(RGB8 { r: 50, g: 0, b: 0 })?;
            bail!("Could not connect to Wifi: {:?}", err)
        }
    };
    let conf  = esp_idf_svc::mqtt::client::MqttClientConfiguration::default();
    let led = led_rc.clone();
    let mut client = EspMqttClient::new("mqtt://47.113.224.100",&conf,
    move |message_event| match message_event {
        Ok(Received(msg)) => {
            match msg.details() {
                Complete => {
                    // println!("{:?}",msg);
                    let message_data: &[u8] = msg.data();
                    // println!("{:?}",message_data);
                    if let Ok(str_convert) = str::from_utf8(message_data) {
                        let rgb_str:Vec<&str> = str_convert.split(",").collect();
                        led.lock().unwrap().set_pixel(rgb::RGB { r: rgb_str[0].parse().unwrap(), g: rgb_str[1].parse().unwrap(), b: rgb_str[2].parse().unwrap() }).unwrap();
                    }
                },
                _=> println!("Could not set board LED"),
            }
        },
        _ => ()
    },
    )?;
    client.subscribe("led", QoS::AtLeastOnce)?;

    let mut ecg_values = [0u8;500];
    // let test_values = [0u8;1000];
    led_rc.clone().lock().unwrap().set_pixel(RGB8 { r: 0, g: 50, b: 0 })?;
    // let mut is_high_q = false;
    loop {
        for i in 0..ecg_values.len()/2 {
            // if i % 2 == 1{
            //     continue;
            // }
            let value_v = adc.read(&mut adc_pin)?;
            // is_high_q = value_v > 500;
            let slice = &mut ecg_values[2*i..2*i+2];
            slice[0] = value_v.to_be_bytes()[0];
            slice[1] = value_v.to_be_bytes()[1];
            
            // let data = u16::from_be_bytes(slice.try_into()?);
            // println!("{value_v}");
            
            FreeRtos::delay_ms(2);
        }
        // if is_high_q {
            client.publish("ecg", QoS::AtMostOnce, false, &ecg_values)?;
        // }
    }

}