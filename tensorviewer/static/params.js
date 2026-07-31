let paramsTimer = null;

let editingParam = null;



function $(id){

    return document.getElementById(id);

}



// --------------------------------------------------
// load
// --------------------------------------------------

async function loadParams(){

    try{


        const r = await fetch(
            "/params",
            {
                cache:"no-store"
            }
        );


        const data =
            await r.json();


        renderParams(data);


    }
    catch(e){

        console.log(
            "params error",
            e
        );

    }

}




// --------------------------------------------------
// render
// --------------------------------------------------

function renderParams(data){


    const table =
        $("params-table");


    if(!table)
        return;



    const active =
        editingParam;



    for(
        const name in data
    ){


        let row =
            document.getElementById(
                "param-" + name
            );



        if(!row){


            row =
                document.createElement(
                    "div"
                );


            row.className =
                "param-row";


            row.id =
                "param-" + name;



            const key =
                document.createElement(
                    "div"
                );


            key.className =
                "param-key";


            key.textContent =
                name;



            const value =
                document.createElement(
                    "input"
                );


            value.className =
                "param-value";


            value.dataset.name =
                name;



            value.addEventListener(
                "focus",
                ()=>{

                    editingParam =
                        name;

                }
            );



            value.addEventListener(
                "blur",
                ()=>{

                    editingParam =
                        null;

                }
            );



            value.addEventListener(
                "change",
                async ()=>{


                    await setParam(

                        name,

                        value.value

                    );


                }
            );



            row.appendChild(
                key
            );


            row.appendChild(
                value
            );


            table.appendChild(
                row
            );

        }



        const input =
            row.querySelector(
                "input"
            );



        if(
            active === name
        ){

            continue;

        }



        let value =
            data[name].value;



        if(
            typeof value === "object"
        ){

            value =
                JSON.stringify(
                    value
                );

        }



        input.value =
            value;



        input.dataset.type =
            data[name].type;


    }



    // удаляем старые параметры

    for(
        const row of
        Array.from(
            table.children
        )
    ){

        const name =
            row.id.replace(
                "param-",
                ""
            );


        if(
            !data[name]
        ){

            row.remove();

        }

    }

}




// --------------------------------------------------
// set
// --------------------------------------------------

async function setParam(
        name,
        value
){


    try{


        await fetch(

            "/params/" + name,

            {

                method:"POST",

                headers:{

                    "Content-Type":
                    "application/json"

                },


                body:
                    JSON.stringify(
                        value
                    )

            }

        );


    }
    catch(e){

        console.log(
            "set param error",
            e
        );

    }

}





// --------------------------------------------------
// start
// --------------------------------------------------

function startParams(){


    loadParams();



    paramsTimer =
        setInterval(

            loadParams,

            1000

        );

}



window.addEventListener(

    "load",

    startParams

);