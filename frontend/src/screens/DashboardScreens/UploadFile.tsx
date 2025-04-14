/**
 * Author: Md Jakaria
 * Date: 2025-04-13
 * Description: This component allows users to upload a file, read its content, and send the text to the backend.
 */

import { useState } from "react";
import Swal from "sweetalert2";
import http from "utils/api";
import "./styles.scss";

/**
 * UploadFile Component
 *
 * This component provides a user interface for uploading a `.txt` file, reading its content,
 * and sending the text to the backend for processing. The backend processes the text and
 * creates a new deck based on the file's content.
 *
 * Features:
 * - File selection with validation for `.txt` files.
 * - Reads the file content on the client side.
 * - Sends the text content to the backend via an HTTP POST request.
 * - Provides success and error feedback to the user using Swal alerts.
 * - Redirects the user to the dashboard upon successful processing.
 *
 * @component
 */
const UploadFile = () => {
  const [fileContent, setFileContent] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const flashCardUser = window.localStorage.getItem("flashCardUser");
  const { localId } = (flashCardUser && JSON.parse(flashCardUser)) || {};

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];

      // Validate file type
      if (file.type !== "text/plain") {
        Swal.fire({
          icon: "error",
          title: "Invalid File Type!",
          text: "Please upload a valid .txt file.",
          confirmButtonColor: "#221daf",
        });
        return;
      }

      // Read the file content
      const reader = new FileReader();
      reader.onload = () => {
        if (reader.result) {
          setFileContent(reader.result.toString());
        }
      };
      reader.onerror = () => {
        Swal.fire({
          icon: "error",
          title: "File Read Error!",
          text: "An error occurred while reading the file. Please try again.",
          confirmButtonColor: "#221daf",
        });
      };
      reader.readAsText(file);
    }
  };

  const handleUploadFile = async (e: any) => {
    e.preventDefault();

    if (!fileContent) {
      Swal.fire({
        icon: "error",
        title: "No File Content!",
        text: "Please select a file and ensure it has valid content.",
        confirmButtonColor: "#221daf",
      });
      return;
    }

    setIsSubmitting(true);

    const payload = {
      text: fileContent,
      localId,
    };

    await http
      .post("/api/upload", payload)
      .then((res) => {
        Swal.fire({
          icon: "success",
          title: "Text Uploaded Successfully!",
          text: "Your text has been processed, and a new deck has been created.",
          confirmButtonColor: "#221daf",
        }).then(() => {
          setIsSubmitting(false);
          window.location.replace(`/dashboard`);
        });
      })
      .catch((err) => {
        Swal.fire({
          icon: "error",
          title: "Upload Failed!",
          text: "An error occurred while processing your text. Please try again.",
          confirmButtonColor: "#221daf",
        });
        setIsSubmitting(false);
      });
  };

  return (
    <div className="create-deck-page dashboard-commons">
      <section>
        <div className="container">
          <div className="row justify-content-center">
            <div className="col-md-6">
              <div className="header-card">
                <div className="row justify-content-center">
                  <div className="col-md-12">
                    <div className="page-header">
                      <div className="row justify-content-between align-items-center">
                        <h3>Upload a File to Create a Deck</h3>
                        <p className="text-muted">
                          Once you upload a file, our system will process its content to create
                          a new deck of flashcards. Ensure the file is in the correct format
                          for accurate processing.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flash-card__list row justify-content-center mt-2">
                  <form className="col-md-12" onSubmit={handleUploadFile}>
                    <div className="form-group">
                      <label>Upload File</label>
                      <input
                        type="file"
                        className="form-control"
                        onChange={handleFileChange}
                        accept=".txt"
                        required
                      />
                    </div>
                    <div className="form-group mt-4 text-right mb-0">
                      <button className="btn" type="submit" disabled={isSubmitting}>
                        <i className="lni lni-upload mr-2"></i>
                        <span className="">
                          {isSubmitting ? "Uploading Text..." : "Upload Text"}
                        </span>
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default UploadFile;