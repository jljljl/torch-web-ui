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


let imagePending = false;
let imageDirty = false;
let lastImageTime = 0;

const IMAGE_FPS = 60;
const IMAGE_INTERVAL = 1000 / IMAGE_FPS;


let statePending = false;



function $(id){
    return document.getElementById(id);
}



function log(...args){

    console.log(...args);

    const box = $("console");

    if(!box)
        return;

    const row = document.createElement("div");

    row.textContent = args.join(" ");

    box.appendChild(row);

    while(box.children.length > 200)
        box.removeChild(box.firstChild);

    box.scrollTop = box.scrollHeight;
}





async function fetchState(){

    if(statePending)
        return;


    statePending = true;


    try{

        const r = await fetch(
            "/state",
            {
                cache:"no-store"
            }
        );


        tensors = await r.json();


        for(const name in tensors){

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
    finally{

        statePending = false;

    }

}





function updateTensorList(){

    const select = $("tensorSelect");

    if(!select)
        return;


    const old = selectedTensor;


    select.innerHTML = "";


    for(const name in tensors){

        const o =
            document.createElement(
                "option"
            );


        o.value = name;


        o.textContent =
            name +
            " " +
            JSON.stringify(
                tensors[name].shape
            );


        select.appendChild(o);

    }


    if(old && tensors[old]){

        selectedTensor = old;

    }
    else{

        selectedTensor =
            Object.keys(tensors)[0] || null;

    }


    select.value =
        selectedTensor || "";


    updateSliders();

}





function updateSliders(){

    if(!selectedTensor)
        return;


    const info =
        tensors[selectedTensor];


    if(!info || !info.shape)
        return;


    const shape =
        info.shape;


    const batch=$("batchSlider");
    const channel=$("channelSlider");


    if(batch){

        batch.max =
            Math.max(
                0,
                shape[0]-1
            );


        if(settings.batch > batch.max)
            settings.batch=0;


        batch.value =
            settings.batch;

    }



    if(channel){

        channel.max =
            Math.max(
                0,
                shape[1]-1
            );


        if(settings.channel > channel.max)
            settings.channel=0;


        channel.value =
            settings.channel;

    }


    $("batchValue").textContent =
        settings.batch;


    $("channelValue").textContent =
        settings.channel;

}





function requestImage(){

    imageDirty=true;


    const now =
        performance.now();


    const delay =
        IMAGE_INTERVAL -
        (now-lastImageTime);


    if(delay <= 0){

        updateImage();

    }
    else{

        setTimeout(
            updateImage,
            delay
        );

    }

}





function updateImage(){

    if(!imageDirty)
        return;


    if(imagePending)
        return;


    if(!selectedTensor)
        return;


    imageDirty=false;

    lastImageTime =
        performance.now();


    const img =
        $("tensorImage");


    if(!img)
        return;



    const p =
        new URLSearchParams();


    p.set(
        "mode",
        settings.mode
    );

    p.set(
        "batch",
        settings.batch
    );

    p.set(
        "channel",
        settings.channel
    );

    p.set(
        "axes",
        settings.axes
    );

    p.set(
        "separate_norm",
        settings.separate_norm
    );

    p.set(
        "version",
        tensorVersions[selectedTensor] || 0
    );



    const url =
        "/tensor/" +
        encodeURIComponent(selectedTensor) +
        "/image?" +
        p.toString();



    imagePending=true;


    const done=()=>{

        imagePending=false;


        if(imageDirty)
            requestImage();

    };


    img.onload=done;
    img.onerror=done;


    img.src=url;

}







function connectWS(){

    const proto =
        location.protocol==="https:"
        ?
        "wss"
        :
        "ws";


    const ws =
        new WebSocket(
            proto+
            "://"+
            location.host+
            "/events"
        );



    ws.onmessage=e=>{


        let msg;


        try{

            msg=JSON.parse(e.data);

        }
        catch{

            return;

        }



        if(
            msg.type !==
            "tensor_update"
        )
            return;



        tensorVersions[msg.tensor]=
            msg.version;



        fetchState();



        if(
            msg.tensor===selectedTensor
        ){

            requestImage();

        }

    };



    ws.onclose=()=>{

        setTimeout(
            connectWS,
            1000
        );

    };

}





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

            requestImage();

        }
    );



    $("modeSelect")
    ?.addEventListener(
        "change",
        e=>{

            settings.mode =
                e.target.value;

            requestImage();

        }
    );



    $("batchSlider")
    ?.addEventListener(
        "input",
        e=>{

            settings.batch =
                Number(e.target.value);


            $("batchValue").textContent =
                settings.batch;


            requestImage();

        }
    );



    $("channelSlider")
    ?.addEventListener(
        "input",
        e=>{

            settings.channel =
                Number(e.target.value);


            $("channelValue").textContent =
                settings.channel;


            requestImage();

        }
    );



    $("axesInput")
    ?.addEventListener(
        "change",
        e=>{

            settings.axes =
                e.target.value;


            requestImage();

        }
    );



    $("separateNorm")
    ?.addEventListener(
        "change",
        e=>{

            settings.separate_norm =
                e.target.checked;


            requestImage();

        }
    );

}





window.addEventListener(
    "load",
    async ()=>{

        initControls();

        await fetchState();

        requestImage();

        connectWS();

    }
);