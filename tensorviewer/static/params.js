let paramsTimer = null;
let editingParam = null;


async function loadParams() {

    try {

        const r = await fetch("/params");

        const data = await r.json();


        updateParams(data);


    } catch(e) {

        console.log(
            "params error",
            e
        );

    }
}



function createParamRow(
        table,
        name,
        param
) {

    const row = document.createElement("div");

    row.className = "param-row";

    row.dataset.name = name;



    const key = document.createElement("div");

    key.className = "param-key";

    key.innerText = name;



    const value = document.createElement("input");

    value.className = "param-value";

    value.dataset.name = name;

    value.dataset.type = param.type;


    value.value = param.value ?? "";



    value.onfocus = function() {

        editingParam = name;

    };



    value.onblur = function() {

        if (editingParam === name)
            editingParam = null;

        setParam(
            name,
            this.value
        );

    };



    if (
        param.type === "int" ||
        param.type === "float"
    ) {

        value.oninput = function() {

            this.value =
                this.value.replace(
                    /[^0-9eE+\-.]/g,
                    ""
                );

        };

    }



    row.appendChild(key);

    row.appendChild(value);


    table.appendChild(row);

}



function updateParams(data) {

    const table = document.getElementById(
        "params-table"
    );


    if (!table)
        return;



    for (const name in data) {


        const param = data[name];


        let input = document.querySelector(
            `.param-value[data-name="${name}"]`
        );



        if (!input) {

            createParamRow(
                table,
                name,
                param
            );

            continue;

        }



        // не трогаем редактируемое поле

        if (
            editingParam === name ||
            document.activeElement === input
        ) {

            continue;

        }



        input.value = param.value ?? "";

        input.dataset.type = param.type;

    }

}



async function setParam(
        name,
        value
) {

    try {

        await fetch(
            "/params/" + encodeURIComponent(name),
            {

                method:"POST",

                headers:{
                    "Content-Type":"application/json"
                },

                body:JSON.stringify(value)

            }
        );


    }
    catch(e) {

        console.log(
            "set param error",
            e
        );

    }

}



function startParams() {

    loadParams();


    paramsTimer = setInterval(
        loadParams,
        1000
    );

}



window.addEventListener(
    "load",
    startParams
);