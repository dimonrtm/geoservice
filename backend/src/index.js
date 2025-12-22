const http = require("http")

const server = http.createServer((req, res) =>{
	const host = req.headers.host ?? "localhost";
	const url = new URL(req.url ?? "/", `http://${host}`);
	const path = url.pathname;
	if(req.method !== "GET"){
		res.statusCode = 405;
		res.setHeader("Content-Type", "text/plain; charset=utf-8");
        res.end("Method Not Allowed");
        return;
	}

	if(path === "/"){
		res.statusCode = 200;
        res.setHeader("Content-Type", "text/plain; charset=utf-8");
        res.end("Hello");
        return;
	}

	if (path === "/health") {
    res.statusCode = 200;
    res.setHeader("Content-Type", "text/plain; charset=utf-8");
    res.end("OK");
    return;
  }

  res.statusCode = 404;
  res.setHeader("Content-Type", "text/plain; charset=utf-8");
  res.end("Not Found");
});

server.listen(3000, "0.0.0.0", () =>{
	console.log("Server is listening on http://localhost:3000");
});
