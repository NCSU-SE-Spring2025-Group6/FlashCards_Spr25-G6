/**
 * Author: Md Jakaria
 * Date: 2025-04-13
 * Description: This component allows users to upload a file to create a new deck.
 */

import { useState } from "react";
import Swal from "sweetalert2";
import http from "utils/api";
import "./styles.scss";

/**
 * UploadFile Component
 *
 * This component provides a user interface for uploading a file to create a new deck.
 * Users can select a `.txt` file from their local system, which will then be uploaded
 * to the server for processing. Upon successful upload, the server processes the file
 * and creates a new deck based on the file's content.
 *
 * Features:
 * - File selection with validation for `.txt` files.
 * - Displays a loading state while the file is being uploaded.
 * - Provides success and error feedback to the user using Swal alerts.
 * - Redirects the user to the dashboard upon successful file upload and deck creation.
 *
 * How it works:
 * 1. The user selects a `.txt` file using the file input field.
 * 2. The selected file is stored in the component's state.
 * 3. Upon form submission, the file is sent to the server via an HTTP POST request.
 * 4. The server processes the file and creates a new deck.
 * 5. If the upload is successful, the user is notified and redirected to the dashboard.
 * 6. If the upload fails, an error message is displayed to the user.
 *
 * @component
 */
const UploadFile = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const flashCardUser = window.localStorage.getItem("flashCardUser");
  const { localId } = (flashCardUser && JSON.parse(flashCardUser)) || {};

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
    }
  };

  const handleUploadFile = async (e: any) => {
    e.preventDefault();

    if (!file) {
      Swal.fire({
        icon: "error",
        title: "No File Selected!",
        text: "Please select a file to upload.",
        confirmButtonColor: "#221daf",
      });
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("localId", localId);

    setIsSubmitting(true);

    await http
      .post("/api/upload", formData)
      .then((res) => {
        Swal.fire({
          icon: "success",
          title: "File Uploaded Successfully!",
          text: "Your file has been processed, and a new deck has been created.",
          confirmButtonColor: "#221daf",
        }).then(() => {
          setIsSubmitting(false);
          window.location.replace(`/dashboard`);
        });
      })
      .catch((err) => {
        Swal.fire({
          icon: "error",
          title: "File Upload Failed!",
          text: "An error occurred while processing your file. Please try again.",
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
                      <button className="btn" type="submit">
                        <i className="lni lni-upload mr-2"></i>
                        <span className="">
                          {isSubmitting ? "Uploading File..." : "Upload File"}
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