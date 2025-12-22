const http = require("http")

const server = http.createServer((req, res) =>{
	res.statusCode = 200;
	res.setHeader("Content-Type", "text/plain; charset=utf-8");
	res.end("Hello from server")
});

server.listen(3000, "0.0.0.0", () =>{
	console.log("Server is listening on http://localhost:3000");
});
