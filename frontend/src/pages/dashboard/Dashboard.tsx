import { motion } from "motion/react";
import { useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  ArrowUpRight,
  CheckCircle2,
  Clock3,
  FileText,
  History,
  ScanLine,
  ShieldCheck,
  Upload,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";

import api from "../../services/api";


interface User {
  id: number;
  name: string;
  email: string;
}


interface Analysis {
  id: number;
  filename: string;
  product_name: string | null;
  mrp: string | null;
  net_quantity: string | null;
  manufacturer: string | null;
  marketer: string | null;
  batch_number: string | null;
  manufacture_date: string | null;
  use_by_date: string | null;
  license_number: string | null;
  overall_status: string | null;
  risk_level: string | null;
  compliance_score: number | null;
  report_path: string | null;
  created_at: string;
}


interface HistoryResponse {
  count: number;
  history: Analysis[];
}


const emptyStats = [
  {
    label: "Labels analyzed",
    value: "0",
    change: "No analyses yet",
    icon: ScanLine,
  },
  {
    label: "Compliant",
    value: "0",
    change: "No data yet",
    icon: CheckCircle2,
  },
  {
    label: "Needs review",
    value: "0",
    change: "No pending reviews",
    icon: AlertTriangle,
  },
  {
    label: "Avg. compliance",
    value: "0%",
    change: "No data yet",
    icon: ShieldCheck,
  },
];


export default function Dashboard() {
  const navigate = useNavigate();

  const fileInputRef =
    useRef<HTMLInputElement>(null);

  const [isDragging, setIsDragging] =
    useState(false);

  const [user, setUser] =
    useState<User | null>(null);

  const [analyses, setAnalyses] =
    useState<Analysis[]>([]);

  const [isLoading, setIsLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);


  // ============================================================
  // LOAD DASHBOARD DATA
  // ============================================================

  useEffect(() => {
    async function loadDashboard() {
      try {
        setIsLoading(true);
        setError(null);

        const [meResponse, historyResponse] =
          await Promise.all([
            api.get("/auth/me"),
            api.get<HistoryResponse>("/history/"),
          ]);

        setUser(meResponse.data.user);

        setAnalyses(
          historyResponse.data.history || []
        );
      } catch (err) {
        console.error(
          "Dashboard loading failed:",
          err
        );

        setError(
          "Unable to load dashboard data. Please try again."
        );
      } finally {
        setIsLoading(false);
      }
    }

    loadDashboard();
  }, []);


  // ============================================================
  // CALCULATE STATISTICS
  // ============================================================

  const totalAnalyses =
    analyses.length;

  const compliantAnalyses =
    analyses.filter((analysis) => {
      const status =
        analysis.overall_status
          ?.toLowerCase()
          .trim();

      return (
        status === "compliant" ||
        status === "pass" ||
        status === "passed"
      );
    }).length;


  const needsReview =
    analyses.filter((analysis) => {
      const status =
        analysis.overall_status
          ?.toLowerCase()
          .trim();

      return (
        status !== "compliant" &&
        status !== "pass" &&
        status !== "passed"
      );
    }).length;


  const scores = analyses
    .map(
      (analysis) =>
        analysis.compliance_score
    )
    .filter(
      (score): score is number =>
        typeof score === "number"
    );


  const averageScore =
    scores.length > 0
      ? Math.round(
          scores.reduce(
            (sum, score) =>
              sum + score,
            0
          ) / scores.length
        )
      : 0;


  const stats = [
    {
      label: "Labels analyzed",
      value: String(totalAnalyses),
      change:
        totalAnalyses > 0
          ? "Total analyses"
          : "No analyses yet",
      icon: ScanLine,
    },
    {
      label: "Compliant",
      value: String(compliantAnalyses),
      change:
        totalAnalyses > 0
          ? `${Math.round(
              (compliantAnalyses /
                totalAnalyses) *
                100
            )}% of analyses`
          : "No data yet",
      icon: CheckCircle2,
    },
    {
      label: "Needs review",
      value: String(needsReview),
      change:
        needsReview > 0
          ? "Potential issues"
          : "All clear",
      icon: AlertTriangle,
    },
    {
      label: "Avg. compliance",
      value: `${averageScore}%`,
      change:
        scores.length > 0
          ? `${scores.length} scored analyses`
          : "No data yet",
      icon: ShieldCheck,
    },
  ];


  // ============================================================
  // FORMAT USER NAME
  // ============================================================

  const displayName =
    user?.name?.trim() || "User";


  // ============================================================
  // FORMAT DATE
  // ============================================================

  function formatDate(
    dateString: string
  ) {
    const date =
      new Date(dateString);

    if (Number.isNaN(date.getTime())) {
      return "Unknown date";
    }

    return date.toLocaleString(
      "en-IN",
      {
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
      }
    );
  }


  // ============================================================
  // OPEN FILE PICKER
  // ============================================================

  function openFilePicker() {
    fileInputRef.current?.click();
  }


  // ============================================================
  // HANDLE FILE
  // ============================================================

  function handleFile(
    file?: File
  ) {
    if (!file) return;

    const allowedTypes = [
      "image/jpeg",
      "image/jpg",
      "image/png",
    ];

    if (
      !allowedTypes.includes(
        file.type
      )
    ) {
      alert(
        "Please select a JPG, JPEG or PNG image."
      );

      return;
    }

    if (
      file.size >
      10 * 1024 * 1024
    ) {
      alert(
        "Maximum file size is 10 MB."
      );

      return;
    }

    navigate(
      "/analysis/new",
      {
        state: {
          file,
        },
      }
    );
  }


  // ============================================================
  // FILE INPUT CHANGE
  // ============================================================

  function handleFileChange(
    event: React.ChangeEvent<HTMLInputElement>
  ) {
    const file =
      event.target.files?.[0];

    handleFile(file);

    event.target.value = "";
  }


  // ============================================================
  // DRAG & DROP
  // ============================================================

  function handleDrop(
    event: React.DragEvent<HTMLDivElement>
  ) {
    event.preventDefault();

    setIsDragging(false);

    const file =
      event.dataTransfer.files?.[0];

    handleFile(file);
  }


  // ============================================================
  // LOGOUT
  // ============================================================

  function handleLogout() {
    localStorage.removeItem(
      "smartlabel_token"
    );

    localStorage.removeItem(
      "smartlabel_user"
    );

    navigate(
      "/login",
      {
        replace: true,
      }
    );
  }


  // ============================================================
  // RECENT ANALYSES
  // ============================================================

  const recentAnalyses =
    analyses.slice(0, 3);


  return (
    <main className="dashboard-page">

      {/* Background glow */}
      <div className="dashboard-glow dashboard-glow-one" />

      <div className="dashboard-glow dashboard-glow-two" />


      {/* ======================================================
          HEADER
      ====================================================== */}

      <header className="dashboard-header">

        <div className="dashboard-brand">

          <div className="dashboard-brand-icon">
            <ScanLine size={20} />
          </div>

          <div>
            <strong>
              SmartLabel
            </strong>

            <span>
              AI
            </span>
          </div>

        </div>


        <div className="dashboard-header-actions">

          <motion.button
            className="dashboard-icon-button"
            title="History"
            whileHover={{
              y: -2,
            }}
            whileTap={{
              scale: 0.95,
            }}
            onClick={() =>
              navigate("/history")
            }
          >
            <History size={18} />
          </motion.button>


          <motion.div
            className="dashboard-avatar"
            whileHover={{
              scale: 1.05,
            }}
            title={
              user?.email ||
              "Account"
            }
          >
            {displayName
              .charAt(0)
              .toUpperCase()}
          </motion.div>

        </div>

      </header>


      {/* ======================================================
          MAIN CONTENT
      ====================================================== */}

      <div className="dashboard-content">


        {/* ====================================================
            ERROR
        ==================================================== */}

        {error && (
          <motion.div
            className="dashboard-error"
            initial={{
              opacity: 0,
              y: -10,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
          >
            <AlertTriangle
              size={18}
            />

            <span>
              {error}
            </span>

            <button
              onClick={() =>
                window.location.reload()
              }
            >
              Retry
            </button>
          </motion.div>
        )}


        {/* ====================================================
            WELCOME
        ==================================================== */}

        <motion.section
          className="dashboard-welcome"
          initial={{
            opacity: 0,
            y: 15,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
          transition={{
            duration: 0.5,
          }}
        >

          <div>

            <div className="dashboard-eyebrow">
              <span />
              COMPLIANCE WORKSPACE
            </div>


            <h1>
              Good morning,
              <span>
                {" "}
                {isLoading
                  ? "..."
                  : displayName}.
              </span>
            </h1>


            <p>
              Analyze packaged commodity
              labels and identify potential
              compliance issues.
            </p>

          </div>


          <motion.button
            className="dashboard-upload-button"
            whileHover={{
              y: -2,
            }}
            whileTap={{
              scale: 0.98,
            }}
            onClick={() =>
              navigate("/analysis/new")
            }
          >
            <Upload size={17} />

            Analyze new label
          </motion.button>

        </motion.section>


        {/* ====================================================
            STATS
        ==================================================== */}

        <section className="dashboard-stats">

          {(isLoading
            ? emptyStats
            : stats
          ).map(
            (
              stat,
              index
            ) => {

              const Icon =
                stat.icon;

              return (
                <motion.div
                  key={
                    stat.label
                  }
                  className="stat-card"
                  initial={{
                    opacity: 0,
                    y: 15,
                  }}
                  animate={{
                    opacity: 1,
                    y: 0,
                  }}
                  transition={{
                    duration: 0.45,
                    delay:
                      index * 0.08,
                  }}
                  whileHover={{
                    y: -4,
                  }}
                >

                  <div className="stat-top">

                    <div className="stat-icon">
                      <Icon size={17} />
                    </div>

                    <ArrowUpRight
                      size={15}
                      className="stat-arrow"
                    />

                  </div>


                  <div className="stat-value">
                    {stat.value}
                  </div>


                  <div className="stat-bottom">

                    <span>
                      {stat.label}
                    </span>

                    <small>
                      {stat.change}
                    </small>

                  </div>

                </motion.div>
              );
            }
          )}

        </section>


        {/* ====================================================
            MAIN GRID
        ==================================================== */}

        <section className="dashboard-grid">


          {/* ==================================================
              UPLOAD
          ================================================== */}

          <motion.div
            className="upload-card"
            initial={{
              opacity: 0,
              y: 20,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            transition={{
              duration: 0.55,
              delay: 0.25,
            }}
          >

            <div className="card-heading">

              <div>

                <span className="card-kicker">
                  AI ANALYSIS
                </span>

                <h2>
                  Analyze a label
                </h2>

                <p>
                  Upload a product package
                  image to begin automated
                  compliance screening.
                </p>

              </div>


              <div className="card-heading-icon">
                <ScanLine size={20} />
              </div>

            </div>


            {/* Hidden file input */}

            <input
              ref={fileInputRef}
              type="file"
              accept=".jpg,.jpeg,.png,image/jpeg,image/png"
              hidden
              onChange={
                handleFileChange
              }
            />


            {/* Upload zone */}

            <motion.div
              className={`upload-zone ${
                isDragging
                  ? "upload-zone-dragging"
                  : ""
              }`}
              onDragOver={(
                event
              ) => {
                event.preventDefault();

                setIsDragging(
                  true
                );
              }}
              onDragLeave={() => {
                setIsDragging(
                  false
                );
              }}
              onDrop={
                handleDrop
              }
              onClick={
                openFilePicker
              }
              whileHover={{
                scale: 1.005,
              }}
            >

              <motion.div
                className="upload-icon"
                animate={{
                  y: [
                    0,
                    -5,
                    0,
                  ],
                }}
                transition={{
                  duration: 2.5,
                  repeat:
                    Infinity,
                  ease:
                    "easeInOut",
                }}
              >
                <Upload size={23} />
              </motion.div>


              <strong>
                {isDragging
                  ? "Drop your image here"
                  : "Drop your label image here"}
              </strong>


              <span>
                or click to browse
                from your device
              </span>


              <small>
                JPG, JPEG or PNG ·
                Max 10 MB
              </small>


              <motion.button
                type="button"
                className="browse-button"
                whileHover={{
                  y: -2,
                }}
                whileTap={{
                  scale: 0.97,
                }}
                onClick={(
                  event
                ) => {
                  event.stopPropagation();

                  openFilePicker();
                }}
              >
                Choose image
              </motion.button>

            </motion.div>

          </motion.div>


          {/* ==================================================
              RECENT ANALYSES
          ================================================== */}

          <motion.div
            className="recent-card"
            initial={{
              opacity: 0,
              y: 20,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            transition={{
              duration: 0.55,
              delay: 0.35,
            }}
          >

            <div className="recent-heading">

              <div>

                <span className="card-kicker">
                  ACTIVITY
                </span>

                <h2>
                  Recent analyses
                </h2>

              </div>


              <button
                onClick={() =>
                  navigate(
                    "/history"
                  )
                }
              >
                View all

                <ArrowUpRight
                  size={14}
                />
              </button>

            </div>


            <div className="analysis-list">

              {isLoading ? (

                <div className="analysis-empty">
                  Loading analyses...
                </div>

              ) : recentAnalyses.length === 0 ? (

                <div className="analysis-empty">

                  <FileText
                    size={24}
                  />

                  <span>
                    No analyses yet.
                  </span>

                  <small>
                    Upload your first
                    product label to
                    get started.
                  </small>

                </div>

              ) : (

                recentAnalyses.map(
                  (
                    analysis
                  ) => {

                    const score =
                      analysis.compliance_score ??
                      0;

                    const status =
                      analysis.overall_status
                        ?.toLowerCase()
                        .trim();

                    const isCompliant =
                      status ===
                        "compliant" ||
                      status === "pass" ||
                      status ===
                        "passed";


                    return (
                      <motion.div
                        className="analysis-row"
                        key={
                          analysis.id
                        }
                        whileHover={{
                          x: 4,
                        }}
                        onClick={() =>
                          navigate(
                            `/history/${analysis.id}`
                          )
                        }
                        style={{
                          cursor:
                            "pointer",
                        }}
                      >

                        <div className="analysis-file-icon">
                          <FileText
                            size={17}
                          />
                        </div>


                        <div className="analysis-info">

                          <strong>
                            {analysis.product_name ||
                              analysis.filename ||
                              "Unnamed product"}
                          </strong>


                          <span>
                            <Clock3
                              size={11}
                            />

                            {formatDate(
                              analysis.created_at
                            )}
                          </span>

                        </div>


                        <div
                          className={`analysis-score ${
                            isCompliant
                              ? "score-good"
                              : "score-review"
                          }`}
                        >
                          {score}%
                        </div>

                      </motion.div>
                    );
                  }
                )

              )}

            </div>

          </motion.div>

        </section>


        {/* ====================================================
            BOTTOM INSIGHT
        ==================================================== */}

        <motion.section
          className="dashboard-insight"
          initial={{
            opacity: 0,
          }}
          animate={{
            opacity: 1,
          }}
          transition={{
            duration: 0.5,
            delay: 0.5,
          }}
        >

          <div className="insight-icon">
            <ShieldCheck size={19} />
          </div>


          <div>

            <strong>
              SmartLabel compliance engine
            </strong>

            <p>
              Automated screening checks
              mandatory declarations,
              extracted information,
              readability and potential
              violations.
            </p>

          </div>


          <span className="engine-status">
            <i />
            Engine ready
          </span>

        </motion.section>


        {/* ====================================================
            ACCOUNT / LOGOUT
        ==================================================== */}

        {user && (
          <motion.div
            className="dashboard-account"
            initial={{
              opacity: 0,
            }}
            animate={{
              opacity: 1,
            }}
          >

            <div>
              <strong>
                {user.name}
              </strong>

              <span>
                {user.email}
              </span>
            </div>


            <button
              onClick={
                handleLogout
              }
            >
              Logout
            </button>

          </motion.div>
        )}

      </div>

    </main>
  );
}