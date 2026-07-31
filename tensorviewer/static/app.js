let tensors = {};
let selectedTensor = null;

let settings = {

    mode:"single_bc",

    batch:0,

    channel:0,

    order:"bchw",

    axes:"B,C,H,W",

    separate_norm:false

};


let renderTimer = null;
let rendering = false;

const FPS = 60;
const FRAME = 1000 / FPS;


function $(id){
    return document.getElementById(id);
}



// -----------------------------
// tensors
// -----------------------------

async function loadTensors(){

    try{

        const r =
            await fetch(
                "/tensors",
                {
                    cache:"no-store"
                }
            );

        tensors =
            await r.json();

        renderTensorList();

    }
    catch(e){

        console.log(
            "tensor list error",
            e
        );

    }

}



function renderTensorList(){

    const select =
        $("tensorSelect");

    if(!select)
        return;

    const old =
        selectedTensor;

    select.innerHTML="";

    for(const name in tensors){

        const t =
            tensors[name];

        const option =
            document.createElement(
                "option"
            );

        option.value =
            name;

        option.textContent =
            name +
            " " +
            JSON.stringify(
                t.shape
            );

        select.appendChild(
            option
        );

    }

    if(
        old &&
        tensors[old]
    ){

        selectedTensor =
            old;

    }
    else{

        const keys =
            Object.keys(
                tensors
            );

        selectedTensor =
            keys.length
            ?
            keys[0]
            :
            null;

    }

    select.value =
        selectedTensor || "";

    updateSliders();

    scheduleDraw();

}



// -----------------------------
// sliders
// -----------------------------

function updateSliders(){

    if(!selectedTensor)
        return;

    const t =
        tensors[selectedTensor];

    if(!t)
        return;

    const shape =
        t.shape;

    const batch =
        $("batchSlider");

    const channel =
        $("channelSlider");

    if(batch){

        batch.max =
            Math.max(
                0,
                shape[0]-1
            );

        if(
            settings.batch >
            Number(batch.max)
        )
            settings.batch=0;

        batch.value =
            settings.batch;

        if($("batchValue"))
            $("batchValue").textContent =
                settings.batch;

    }

    if(channel){

        channel.max =
            Math.max(
                0,
                shape[1]-1
            );

        if(
            settings.channel >
            Number(channel.max)
        )
            settings.channel=0;

        channel.value =
            settings.channel;

        if($("channelValue"))
            $("channelValue").textContent =
                settings.channel;

    }

    if($("modeSelect"))
        $("modeSelect").value =
            settings.mode;

    if($("axesInput"))
        $("axesInput").value =
            settings.axes;

    if($("separateNorm"))
        $("separateNorm").checked =
            settings.separate_norm;

}



// -----------------------------
// scheduler
// -----------------------------

function scheduleDraw(){

    if(renderTimer)
        return;

    renderTimer =
        setTimeout(

            ()=>{

                renderTimer=null;

                drawCurrent();

            },

            FRAME

        );

}



// -----------------------------
// tensor loading
// -----------------------------

async function getTile(

    name,
    b,
    c

){

    const url =
        `/tensors/${encodeURIComponent(name)}/get/${b}/${c}/${settings.order}`;

    const r =
        await fetch(
            url,
            {
                cache:"no-store"
            }
        );

    if(!r.ok)
        throw new Error(
            url +
            " " +
            r.status
        );

    const buffer =
        await r.arrayBuffer();

    return{

        buffer,

        batch:b,

        channel:c

    };

}



// -----------------------------
// drawing
// -----------------------------

async function drawCurrent(){

    if(rendering)
        return;

    if(!selectedTensor)
        return;

    rendering=true;

    try{

        const t =
            tensors[selectedTensor];

        if(!t)
            return;

        const shape =
            t.shape;

        const B =
            shape[0];

        const C =
            shape[1];

        const H =
            shape[2];

        const W =
            shape[3];

        const requests=[];

        switch(settings.mode){

            case "single_bc":

                requests.push({

                    b:settings.batch,

                    c:settings.channel

                });

                break;


            case "batch_all_channels":

                for(
                    let c=0;
                    c<C;
                    c++
                ){

                    requests.push({

                        b:settings.batch,

                        c

                    });

                }

                break;


            case "channel_all_batches":

                for(
                    let b=0;
                    b<B;
                    b++
                ){

                    requests.push({

                        b,

                        c:settings.channel

                    });

                }

                break;


            case "grid_bc":

            default:

                for(
                    let b=0;
                    b<B;
                    b++
                ){

                    for(
                        let c=0;
                        c<C;
                        c++
                    ){

                        requests.push({

                            b,

                            c

                        });

                    }

                }

        }

        const tiles=[];

        for(
            const r of requests
        ){

            const raw =
                await getTile(

                    selectedTensor,

                    r.b,

                    r.c

                );

            tiles.push({

                ...raw,

                width:W,

                height:H

            });

        }

        drawTensor(

            tiles,

            {

                mode:settings.mode,

                batch:settings.batch,

                channel:settings.channel,

                separateNorm:
                    settings.separate_norm

            }

        );

    }
    catch(e){

        console.log(
            "draw error",
            e
        );

    }
    finally{

        rendering=false;

    }

}



// -----------------------------
// websocket
// -----------------------------

function connectWS(){

    const proto =
        location.protocol==="https:"
        ?
        "wss"
        :
        "ws";

    const ws =
        new WebSocket(

            proto +
            "://" +
            location.host +
            "/events"

        );

    ws.onmessage =
        e=>{

            try{

                const msg =
                    JSON.parse(
                        e.data
                    );

                if(
                    msg.type==="tensor_update"
                ){

                    loadTensors();

                }

            }
            catch{}

        };

    ws.onclose =
        ()=>{

            setTimeout(

                connectWS,

                1000

            );

        };

}



// -----------------------------
// controls
// -----------------------------

function initControls(){

    $("tensorSelect")
    ?.addEventListener(
        "change",
        e=>{

            selectedTensor =
                e.target.value;

            settings.batch=0;
            settings.channel=0;

            updateSliders();

            scheduleDraw();

        }
    );


    $("modeSelect")
    ?.addEventListener(
        "change",
        e=>{

            settings.mode =
                e.target.value;

            scheduleDraw();

        }
    );


    $("batchSlider")
    ?.addEventListener(
        "input",
        e=>{

            settings.batch =
                Number(
                    e.target.value
                );

            $("batchValue").textContent =
                settings.batch;

            scheduleDraw();

        }
    );


    $("channelSlider")
    ?.addEventListener(
        "input",
        e=>{

            settings.channel =
                Number(
                    e.target.value
                );

            $("channelValue").textContent =
                settings.channel;

            scheduleDraw();

        }
    );


    $("axesInput")
    ?.addEventListener(
        "change",
        e=>{

            settings.axes =
                e.target.value;

        }
    );


    $("separateNorm")
    ?.addEventListener(
        "change",
        e=>{

            settings.separate_norm =
                e.target.checked;

            scheduleDraw();

        }
    );

}



// -----------------------------
// start
// -----------------------------

window.onload =
async()=>{

    initRenderer(
        "tensorCanvas"
    );

    initControls();

    await loadTensors();

    connectWS();

};