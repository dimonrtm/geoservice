const express = require("express");

const app = express();

app.get("/", (req, res) =>{
res.type("text/plain").send("Hello World!");
});

app.get("/users/health", (req, res) =>{
	res.send("ok");
});

app.get("/users/:id", (req, res) => {
res.send(`user ${req.params.id}`);
});

const PORT = process.env.PORT ? Number(process.env.PORT) : 3000;

const HOST = "0.0.0.0";

app.listen(PORT, HOST, () =>{
	console.log(`Server is running on http://localhost:${PORT}/`);
});
