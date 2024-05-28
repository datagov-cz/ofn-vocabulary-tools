function App() {
  return (
    <div>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          const input = document.getElementById(
            "inputFile"
          ) as HTMLInputElement;
          if (input) {
            if (input.files && input.files[0]) {
              input.files[0]
                .text()
                .then((text) => {
                  fetch("http://127.0.0.1:5000/api/test", {
                    method: "POST",
                    headers: {
                      "Content-Type": "text/plain",
                    },
                    body: text,
                  })
                    .then((response) => response.json())
                    .then((json) => {
                      const errorP = document.getElementById("response");
                      if (errorP) errorP.innerHTML = JSON.stringify(json);
                    })
                    .catch((e) => {
                      const errorP = document.getElementById("errorP");
                      if (errorP) errorP.innerHTML = e;
                    });
                })
                .catch((e) => {
                  const errorP = document.getElementById("errorP");
                  if (errorP) errorP.innerHTML = e;
                });
            }
          } else console.error("Could not find <input type=file>");
        }}
      >
        <input type="file" id="inputFile" name="input" />
        <input type="submit" />
      </form>
      <p style={{ color: "red" }} id="errorP"></p>
      <p id="response"></p>
    </div>
  );
}

export default App;
