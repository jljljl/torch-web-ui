// app.js


let tensors = {};

let tensorVersions = {};

let selectedTensor = null;


let settings = {

    mode: "single_bc",

    batch: 0,

    channel: 0,

    axes: "B,C,H,W",

    separate_norm: false

};



function $(id){

    return document.getElementById(id);

}




// --------------------------------------------------
// console
// --------------------------------------------------

function log(...args){

    console.log(...args);


    const box = $("console");


    if(!box)
        return;


    const row =
        document.createElement("div");


    row.textContent =
        args.join(" ");


    box.appendChild(row);


    box.scrollTop =
        box.scrollHeight;

}




// --------------------------------------------------
// state
// --------------------------------------------------

async function fetchState(){

    try{


        const response =
            await fetch(
                "/state",
                {
                    cache:"no-store"
                }
            );


        tensors =
            await response.json();



        for(
            const name in tensors
        ){

            tensorVersions[name] =
                tensors[name].version || 0;

        }



        updateTensorList();



    }
    catch(e){

        log(
            "state error",
            e
        );

    }

}




// --------------------------------------------------
// tensor list
// --------------------------------------------------

function updateTensorList(){


    const select =
        $("tensorSelect");


    if(!select)
        return;



    const previous =
        selectedTensor;



    select.innerHTML = "";



    for(
        const name in tensors
    ){

        const option =
            document.createElement(
                "option"
            );


        option.value =
            name;


        option.textContent =
            name
            +
            " "
            +
            JSON.stringify(
                tensors[name].shape
            );


        select.appendChild(
            option
        );

    }




    if(
        previous &&
        tensors[previous]
    ){

        selectedTensor =
            previous;

    }
    else{


        const names =
            Object.keys(
                tensors
            );


        if(names.length)
            selectedTensor =
                names[0];

    }



    select.value =
        selectedTensor || "";



    updateSliders();

}




// --------------------------------------------------
// sliders
// --------------------------------------------------

function updateSliders(){


    if(!selectedTensor)
        return;



    const info =
        tensors[selectedTensor];


    if(!info || !info.shape)
        return;



    const shape =
        info.shape;



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


        batch.value =
            settings.batch;

    }




    if(channel){

        channel.max =
            Math.max(
                0,
                shape[1]-1
            );


        channel.value =
            settings.channel;

    }



    if(
        settings.batch >
        Number(batch.max)
    ){

        settings.batch=0;

        batch.value=0;

    }



    if(
        settings.channel >
        Number(channel.max)
    ){

        settings.channel=0;

        channel.value=0;

    }



    if($("batchValue"))

        $("batchValue").textContent =
            settings.batch;



    if($("channelValue"))

        $("channelValue").textContent =
            settings.channel;



    log(
        "slider update",
        selectedTensor,
        shape,
        "B:",
        batch ? batch.max : "-",
        "C:",
        channel ? channel.max : "-"
    );

}





// --------------------------------------------------
// websocket
// --------------------------------------------------

function connectWS(){


    const proto =
        location.protocol==="https:"
        ?
        "wss"
        :
        "ws";



    const ws =
        new WebSocket(
            proto
            +
            "://"
            +
            location.host
            +
            "/events"
        );



    ws.onopen = ()=>{

        log(
            "websocket connected"
        );

    };



    ws.onmessage = e=>{


        let msg;


        try{

            msg =
                JSON.parse(
                    e.data
                );

        }
        catch{

            return;

        }



        log(
            "WS",
            JSON.stringify(msg)
        );



        if(
            msg.type !==
            "tensor_update"
        )
            return;



        tensorVersions[msg.tensor] =
            msg.version;



        fetchState();



        if(
            msg.tensor === selectedTensor
        ){

            updateImage();

        }


    };



    ws.onclose = ()=>{

        log(
            "websocket closed"
        );


        setTimeout(
            connectWS,
            1000
        );

    };



    ws.onerror = ()=>{

        log(
            "websocket error"
        );

    };

}





// --------------------------------------------------
// image
// --------------------------------------------------

function updateImage(){


    if(!selectedTensor)
        return;



    const img =
        $("tensorImage");


    if(!img)
        return;



    const params =
        new URLSearchParams();



    params.set(
        "mode",
        settings.mode
    );


    params.set(
        "batch",
        settings.batch
    );


    params.set(
        "channel",
        settings.channel
    );


    params.set(
        "axes",
        settings.axes
    );


    params.set(
        "separate_norm",
        settings.separate_norm
    );


    params.set(
        "version",
        tensorVersions[selectedTensor] || 0
    );



    const url =
        "/tensor/"
        +
        encodeURIComponent(
            selectedTensor
        )
        +
        "/image?"
        +
        params.toString();



    log(
        "image",
        url
    );



    img.src =
        url;

}





// --------------------------------------------------
// controls
// --------------------------------------------------

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


            updateImage();


        }
    );





    $("modeSelect")
    ?.addEventListener(
        "change",
        e=>{


            settings.mode =
                e.target.value;


            updateImage();


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


            updateImage();

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


            updateImage();

        }
    );





    $("axesInput")
    ?.addEventListener(
        "change",
        e=>{


            settings.axes =
                e.target.value;


            updateImage();

        }
    );





    $("separateNorm")
    ?.addEventListener(
        "change",
        e=>{


            settings.separate_norm =
                e.target.checked;


            updateImage();

        }
    );


}





// --------------------------------------------------
// start
// --------------------------------------------------

window.addEventListener(
    "load",
    async ()=>{


        log(
            "starting viewer"
        );


        initControls();


        await fetchState();


        updateImage();


        connectWS();


    }
);