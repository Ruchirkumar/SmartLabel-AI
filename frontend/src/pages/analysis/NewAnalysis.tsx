import { useRef, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  FileImage,
  ImagePlus,
  LoaderCircle,
  ScanLine,
  ShieldCheck,
  Sparkles,
  Upload,
  X,
  AlertCircle,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import api from "../../services/api";

type AnalysisStep = "upload" | "processing" | "error";

const processingSteps = [
  "Checking image quality",
  "Running OCR",
  "Extracting declarations",
  "Running compliance checks",
];

export default function NewAnalysis() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);

  const [step, setStep] = useState<AnalysisStep>("upload");
  const [processingIndex, setProcessingIndex] = useState(0);

  const [errorMessage, setErrorMessage] = useState("");

  const [dragActive, setDragActive] = useState(false);

  // --------------------------------------------------
  // FILE VALIDATION
  // --------------------------------------------------

  function validateFile(selectedFile: File): boolean {
    const allowedTypes = [
      "image/jpeg",
      "image/png",
      "image/webp",
    ];

    if (!allowedTypes.includes(selectedFile.type)) {
      setErrorMessage(
        "Only JPG, JPEG, PNG and WEBP images are allowed."
      );
      setStep("error");
      return false;
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
      setErrorMessage(
        "Image size must be less than 10 MB."
      );
      setStep("error");
      return false;
    }

    return true;
  }

  // --------------------------------------------------
  // SELECT FILE
  // --------------------------------------------------

  function selectFile(selectedFile: File) {
    if (!validateFile(selectedFile)) {
      return;
    }

    if (preview) {
      URL.revokeObjectURL(preview);
    }

    const objectUrl = URL.createObjectURL(selectedFile);

    setFile(selectedFile);
    setPreview(objectUrl);

    setErrorMessage("");
    setStep("upload");
    setProcessingIndex(0);
  }

  function handleFileChange(
    event: React.ChangeEvent<HTMLInputElement>
  ) {
    const selectedFile = event.target.files?.[0];

    if (!selectedFile) {
      return;
    }

    selectFile(selectedFile);
  }

  // --------------------------------------------------
  // DRAG & DROP
  // --------------------------------------------------

  function handleDragOver(
    event: React.DragEvent<HTMLDivElement>
  ) {
    event.preventDefault();
    event.stopPropagation();
    setDragActive(true);
  }

  function handleDragLeave(
    event: React.DragEvent<HTMLDivElement>
  ) {
    event.preventDefault();
    event.stopPropagation();
    setDragActive(false);
  }

  function handleDrop(
    event: React.DragEvent<HTMLDivElement>
  ) {
    event.preventDefault();
    event.stopPropagation();

    setDragActive(false);

    const droppedFile =
      event.dataTransfer.files?.[0];

    if (!droppedFile) {
      return;
    }

    selectFile(droppedFile);
  }

  // --------------------------------------------------
  // REMOVE FILE
  // --------------------------------------------------

  function removeFile() {
    if (preview) {
      URL.revokeObjectURL(preview);
    }

    setFile(null);
    setPreview(null);

    setStep("upload");
    setProcessingIndex(0);
    setErrorMessage("");

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  // --------------------------------------------------
  // GET BACKEND ERROR
  // --------------------------------------------------

  function getErrorMessage(error: unknown): string {
    if (
      typeof error === "object" &&
      error !== null &&
      "response" in error
    ) {
      const axiosError = error as {
        response?: {
          data?: {
            detail?: string;
          };
          status?: number;
        };
        message?: string;
      };

      const detail =
        axiosError.response?.data?.detail;

      if (detail) {
        return detail;
      }

      if (axiosError.response?.status === 401) {
        return "Your session has expired. Please log in again.";
      }

      if (axiosError.response?.status === 404) {
        return "The uploaded image could not be found by the analysis server.";
      }

      if (axiosError.response?.status === 500) {
        return "The server encountered an error while analyzing the image.";
      }

      if (axiosError.message) {
        return axiosError.message;
      }
    }

    if (error instanceof Error) {
      return error.message;
    }

    return "Something went wrong while analyzing the image.";
  }

  // --------------------------------------------------
  // REAL ANALYSIS
  // --------------------------------------------------

  async function startAnalysis() {
    if (!file) {
      return;
    }

    setStep("processing");
    setProcessingIndex(0);
    setErrorMessage("");

    try {
      // ----------------------------------------------
      // STEP 1 — UPLOAD IMAGE
      // ----------------------------------------------

      const formData = new FormData();

      formData.append("file", file);

      const uploadResponse = await api.post(
        "/upload",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      const uploadData = uploadResponse.data;

      const filename =
        uploadData?.filename;

      if (!filename) {
        throw new Error(
          "Upload succeeded but the server did not return a filename."
        );
      }

      // ----------------------------------------------
      // STEP 2 — QUALITY CHECK
      // ----------------------------------------------

      setProcessingIndex(0);

      await new Promise((resolve) =>
        setTimeout(resolve, 400)
      );

      // ----------------------------------------------
      // STEP 3 — REAL BACKEND ANALYSIS
      // ----------------------------------------------

      setProcessingIndex(1);

      const analysisResponse = await api.post(
        `/analyze-image/${encodeURIComponent(filename)}`
      );

      const analysisData =
        analysisResponse.data;

      // ----------------------------------------------
      // EXTRACTION / COMPLIANCE UI PROGRESS
      // ----------------------------------------------

      setProcessingIndex(2);

      await new Promise((resolve) =>
        setTimeout(resolve, 300)
      );

      setProcessingIndex(3);

      await new Promise((resolve) =>
        setTimeout(resolve, 300)
      );

      // ----------------------------------------------
      // GET DATABASE ANALYSIS ID
      // ----------------------------------------------

      const analysisId =
        analysisData?.analysis_id;

      if (!analysisId) {
        throw new Error(
          "Analysis completed but no analysis ID was returned by the server."
        );
      }

      // ----------------------------------------------
      // OPEN RESULT PAGE
      // ----------------------------------------------

      navigate(`/analysis/${analysisId}`);

    } catch (error) {
      console.error(
        "SmartLabel analysis error:",
        error
      );

      setErrorMessage(
        getErrorMessage(error)
      );

      setStep("error");
    }
  }

  // --------------------------------------------------
  // RETRY
  // --------------------------------------------------

  function retryAnalysis() {
    setErrorMessage("");
    setStep("upload");
    setProcessingIndex(0);
  }

  // --------------------------------------------------
  // RENDER
  // --------------------------------------------------

  return (
    <main className="analysis-page">

      {/* ==========================================
          HEADER
      ========================================== */}

      <header className="analysis-header">

        <Link
          to="/dashboard"
          className="analysis-back"
        >
          <ArrowLeft size={16} />
          Dashboard
        </Link>

        <div className="analysis-title">

          <div className="analysis-title-icon">
            <ScanLine size={18} />
          </div>

          <div>
            <strong>
              New Analysis
            </strong>

            <span>
              SmartLabel AI
            </span>
          </div>

        </div>

        <div className="analysis-secure">
          <ShieldCheck size={14} />
          Secure analysis
        </div>

      </header>

      {/* ==========================================
          MAIN CONTENT
      ========================================== */}

      <div className="analysis-content">

        {/* ======================================
            INTRO
        ====================================== */}

        <motion.div
          className="analysis-intro"
          initial={{
            opacity: 0,
            y: 15,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
        >

          <div className="analysis-eyebrow">
            <Sparkles size={13} />
            AI-POWERED INSPECTION
          </div>

          <h1>
            Analyze your
            <span> product label.</span>
          </h1>

          <p>
            Upload a clear image of the packaged
            commodity label. SmartLabel will
            automatically inspect declarations and
            identify potential compliance issues.
          </p>

        </motion.div>

        <AnimatePresence mode="wait">

          {/* ======================================
              UPLOAD
          ====================================== */}

          {step === "upload" && (

            <motion.div
              key="upload"
              className="analysis-upload-layout"
              initial={{
                opacity: 0,
                y: 15,
              }}
              animate={{
                opacity: 1,
                y: 0,
              }}
              exit={{
                opacity: 0,
                y: -10,
              }}
            >

              <div className="analysis-upload-card">

                <div className="analysis-card-heading">

                  <div>

                    <span>
                      STEP 01
                    </span>

                    <h2>
                      Upload label image
                    </h2>

                    <p>
                      Use a front, back or side
                      package image containing
                      the product declarations.
                    </p>

                  </div>

                  <div className="analysis-card-icon">
                    <ImagePlus size={19} />
                  </div>

                </div>

                {/* --------------------------------
                    DROPZONE
                -------------------------------- */}

                {!preview ? (

                  <div
                    className={`analysis-dropzone ${
                      dragActive
                        ? "drag-active"
                        : ""
                    }`}
                    onClick={() =>
                      fileInputRef.current?.click()
                    }
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                  >

                    <div className="analysis-upload-icon">
                      <Upload size={25} />
                    </div>

                    <strong>
                      Drop your label image here
                    </strong>

                    <span>
                      or click to browse
                    </span>

                    <small>
                      JPG, JPEG, PNG or WEBP · Maximum 10 MB
                    </small>

                    <button
                      type="button"
                      className="analysis-browse"
                      onClick={(event) => {
                        event.stopPropagation();
                        fileInputRef.current?.click();
                      }}
                    >
                      Choose image
                    </button>

                  </div>

                ) : (

                  /* --------------------------------
                     IMAGE PREVIEW
                  -------------------------------- */

                  <div className="image-preview-wrapper">

                    <img
                      src={preview}
                      alt="Selected product label"
                      className="analysis-preview"
                    />

                    <button
                      type="button"
                      className="remove-image"
                      onClick={removeFile}
                      aria-label="Remove image"
                    >
                      <X size={16} />
                    </button>

                    <div className="preview-file-info">

                      <FileImage size={15} />

                      <span>
                        {file?.name}
                      </span>

                    </div>

                  </div>

                )}

                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/png,image/jpeg,image/jpg,image/webp"
                  hidden
                  onChange={handleFileChange}
                />

                {/* --------------------------------
                    START BUTTON
                -------------------------------- */}

                {file && (

                  <motion.button
                    type="button"
                    className="start-analysis-button"
                    onClick={startAnalysis}
                    initial={{
                      opacity: 0,
                      y: 8,
                    }}
                    animate={{
                      opacity: 1,
                      y: 0,
                    }}
                    whileHover={{
                      y: -2,
                    }}
                    whileTap={{
                      scale: 0.985,
                    }}
                  >

                    <span>
                      Start analysis
                    </span>

                    <ArrowRight size={17} />

                  </motion.button>

                )}

              </div>

              {/* ==================================
                  REQUIREMENTS
              ================================== */}

              <div className="analysis-info-card">

                <div className="analysis-info-header">

                  <ShieldCheck size={17} />

                  <strong>
                    For best results
                  </strong>

                </div>

                <div className="analysis-requirements">

                  <div>
                    <CheckCircle2 size={14} />
                    <span>
                      Use a sharp, readable image
                    </span>
                  </div>

                  <div>
                    <CheckCircle2 size={14} />
                    <span>
                      Keep the entire label visible
                    </span>
                  </div>

                  <div>
                    <CheckCircle2 size={14} />
                    <span>
                      Avoid glare and extreme angles
                    </span>
                  </div>

                  <div>
                    <CheckCircle2 size={14} />
                    <span>
                      Ensure declarations are readable
                    </span>
                  </div>

                </div>

                <div className="analysis-pipeline">

                  <span>
                    OCR
                  </span>

                  <i />

                  <span>
                    Extraction
                  </span>

                  <i />

                  <span>
                    Compliance
                  </span>

                </div>

              </div>

            </motion.div>

          )}

          {/* ======================================
              PROCESSING
          ====================================== */}

          {step === "processing" && (

            <motion.div
              key="processing"
              className="processing-card"
              initial={{
                opacity: 0,
                scale: 0.97,
              }}
              animate={{
                opacity: 1,
                scale: 1,
              }}
              exit={{
                opacity: 0,
              }}
            >

              <div className="processing-visual">

                <motion.div
                  className="processing-ring"
                  animate={{
                    rotate: 360,
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "linear",
                  }}
                />

                <ScanLine size={28} />

              </div>

              <div className="processing-heading">

                <span>
                  SMARTLABEL ENGINE
                </span>

                <h2>
                  Analyzing your label
                </h2>

                <p>
                  Please keep this window open
                  while our inspection pipeline
                  processes the image.
                </p>

              </div>

              <div className="processing-steps">

                {processingSteps.map(
                  (item, index) => {

                    const completed =
                      index < processingIndex;

                    const active =
                      index === processingIndex;

                    return (

                      <div
                        className={`processing-step ${
                          completed
                            ? "completed"
                            : ""
                        } ${
                          active
                            ? "active"
                            : ""
                        }`}
                        key={item}
                      >

                        <div className="processing-step-icon">

                          {completed ? (

                            <CheckCircle2 size={15} />

                          ) : active ? (

                            <LoaderCircle
                              size={15}
                              className="spin"
                            />

                          ) : (

                            <span />

                          )}

                        </div>

                        <span>
                          {item}
                        </span>

                        {completed && (

                          <small>
                            Complete
                          </small>

                        )}

                      </div>

                    );

                  }
                )}

              </div>

            </motion.div>

          )}

          {/* ======================================
              ERROR
          ====================================== */}

          {step === "error" && (

            <motion.div
              key="error"
              className="analysis-complete-card"
              initial={{
                opacity: 0,
                scale: 0.96,
              }}
              animate={{
                opacity: 1,
                scale: 1,
              }}
            >

              <div
                className="complete-icon"
                style={{
                  color: "#ff6b6b",
                }}
              >
                <AlertCircle size={29} />
              </div>

              <span className="complete-label">
                ANALYSIS FAILED
              </span>

              <h2>
                We couldn't analyze this image.
              </h2>

              <p>
                {errorMessage ||
                  "Something went wrong while processing the image."}
              </p>

              <div className="complete-actions">

                <button
                  type="button"
                  className="secondary-analysis-button"
                  onClick={retryAnalysis}
                >
                  Try again
                </button>

                <Link
                  to="/dashboard"
                  className="start-analysis-button"
                >
                  Back to dashboard
                  <ArrowRight size={17} />
                </Link>

              </div>

            </motion.div>

          )}

        </AnimatePresence>

      </div>

    </main>
  );
}