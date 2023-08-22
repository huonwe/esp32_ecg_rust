window.onload = function() {
    const img_ecg = document.querySelector("#img_ecg")
    const img_doki = document.querySelector("#img_doki")
    const socket1 = new WebSocket("ws://"+location.host+"/plot")
    socket1.addEventListener('message',ev=>{
        // console.log(ev.data)
        img_ecg.src = "data:;base64,"+ev.data
    })

    const socket2 = new WebSocket("ws://"+location.host+"/neon")
    // socket2.addEventListener('message',ev=>{
    //     // console.log(ev.data)
    //     img_doki.src = "data:;base64,"+ev.data
    // })

    const range_r = document.querySelector("#range_r")
    const range_g = document.querySelector("#range_g")
    const range_b = document.querySelector("#range_b")
    const neon_alert = document.querySelector("#neon_alert")
    range_r.addEventListener("input",ev => {
        socket2.send(`${range_r.value},${range_g.value},${range_b.value}`)
    })
    range_g.addEventListener("input",ev => {
        socket2.send(`${range_r.value},${range_g.value},${range_b.value}`)
    })
    range_b.addEventListener("input",ev => {
        socket2.send(`${range_r.value},${range_g.value},${range_b.value}`)
    })
    neon_alert.addEventListener("click",ev=>{
        range_r.value = 228
        range_g.value = 91
        range_b.value = 91
        socket2.send("228,91,91")
    })
}