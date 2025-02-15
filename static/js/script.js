document.getElementById("uploadForm").addEventListener("submit", async function(event) {
    event.preventDefault();
    
    let fileInput = document.getElementById("fileInput").files[0];
    let plantType = document.getElementById("plantType").value;

    if (!fileInput) {
        alert("Please upload an image.");
        return;
    }

    let formData = new FormData();
    formData.append("file", fileInput);
    formData.append("plant_type", plantType);

    try {
        let response = await fetch("classify", {  // Corrected URL
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            throw new Error("Failed to get a response from the server.");
        }

        let result = await response.json();
        document.getElementById("result").innerText = "Predicted Disease: " + result.predicted_class +
            "\nRecommended Pesticide: " + result.recommended_pesticide;
    } catch (error) {
        console.error("Error:", error);
        document.getElementById("result").innerText = "Error: Could not fetch prediction.";
    }
});
