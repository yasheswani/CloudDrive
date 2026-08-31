import React, { useEffect, useState } from "react";

import { createRoot } from "react-dom/client";

import {
  UploadCloud,
  Folder,
  File,
  Search,
  Star,
  Trash2,
  Users,
  Grid2X2,
  List,
  Download,
  RotateCcw,
  LogOut,
  Plus,
  Share2,
  Cloud,
  ChevronRight,
} from "lucide-react";

import { useDropzone } from "react-dropzone";

import { api } from "./services/api";

import "./styles.css";

/* ========================================================
   HELPERS
======================================================== */

const fmt = (n) => {
  if (n < 1024) {
    return `${n} B`;
  }

  if (n < 1048576) {
    return `${(n / 1024).toFixed(1)} KB`;
  }

  if (n < 1073741824) {
    return `${(n / 1048576).toFixed(1)} MB`;
  }

  return `${(n / 1073741824).toFixed(1)} GB`;
};

/* ========================================================
   AUTH SCREEN
======================================================== */

function Auth({ onLogin }) {
  const [mode, setMode] = useState("login");

  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
  });

  const [err, setErr] = useState("");

  const [loading, setLoading] = useState(false);

  async function go(e) {
    e.preventDefault();

    setErr("");
    setLoading(true);

    try {
      const response = await api.post(
        `/auth/${mode === "login" ? "login" : "register"}`,
        form,
      );

      /*
       * Backend has already created the HttpOnly
       * authentication cookies.
       *
       * We now store only the returned user object
       * in React state.
       */
      onLogin(response.data);
    } catch (error) {
      const detail = error.response?.data?.detail;

      if (Array.isArray(detail)) {
        setErr(detail.map((item) => item.msg).join(", "));
      } else {
        setErr(detail || "Something went wrong");
      }
    } finally {
      setLoading(false);
    }
  }

  function switchMode() {
    setErr("");

    setForm({
      name: "",
      email: "",
      password: "",
    });

    setMode(mode === "login" ? "register" : "login");
  }

  return (
    <div className="auth">
      <div className="auth-card">
        <div className="brand">
          <span className="logo">
            <Cloud size={22} />
          </span>

          <b>CloudDrive</b>
        </div>

        <h1>{mode === "login" ? "Welcome back" : "Create your account"}</h1>

        <p className="muted">Secure storage for your files, anywhere.</p>

        <form onSubmit={go}>
          {mode === "register" && (
            <input
              placeholder="Full name"
              value={form.name}
              onChange={(e) =>
                setForm({
                  ...form,
                  name: e.target.value,
                })
              }
              required
            />
          )}

          <input
            type="email"
            placeholder="Email address"
            value={form.email}
            onChange={(e) =>
              setForm({
                ...form,
                email: e.target.value,
              })
            }
            required
          />

          <input
            type="password"
            placeholder="Password (8+ characters)"
            value={form.password}
            onChange={(e) =>
              setForm({
                ...form,
                password: e.target.value,
              })
            }
            minLength={8}
            required
          />

          {err && <div className="error">{err}</div>}

          <button type="submit" className="primary full" disabled={loading}>
            {loading
              ? "Please wait..."
              : mode === "login"
                ? "Sign in"
                : "Create account"}
          </button>
        </form>

        <div className="switch">
          {mode === "login" ? "New to CloudDrive?" : "Already have an account?"}{" "}
          <button type="button" onClick={switchMode}>
            {mode === "login" ? "Create one" : "Sign in"}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ========================================================
   MAIN APPLICATION
======================================================== */

function App() {
  const [user, setUser] = useState(null);

  const [authChecking, setAuthChecking] = useState(true);

  const [view, setView] = useState("drive");

  const [folder, setFolder] = useState(null);

  const [folders, setFolders] = useState([]);

  const [files, setFiles] = useState([]);

  const [q, setQ] = useState("");

  const [grid, setGrid] = useState(true);

  const [showFolder, setShowFolder] = useState(false);

  const [newFolder, setNewFolder] = useState("");

  const [share, setShare] = useState(null);

  const [shareEmail, setShareEmail] = useState("");

  const [link, setLink] = useState(null);

  const [toast, setToast] = useState("");

  /* ====================================================
       CHECK EXISTING SESSION
    ==================================================== */

  useEffect(() => {
    let mounted = true;

    async function checkSession() {
      try {
        const response = await api.get("/auth/me");

        if (mounted) {
          setUser(response.data);
        }
      } catch {
        if (mounted) {
          setUser(null);
        }
      } finally {
        if (mounted) {
          setAuthChecking(false);
        }
      }
    }

    checkSession();

    return () => {
      mounted = false;
    };
  }, []);

  /* ====================================================
       HANDLE EXPIRED SESSION
    ==================================================== */

  useEffect(() => {
    function handleUnauthorized() {
      setUser(null);

      setFolders([]);
      setFiles([]);
      setFolder(null);
    }

    window.addEventListener("clouddrive:unauthorized", handleUnauthorized);

    return () => {
      window.removeEventListener("clouddrive:unauthorized", handleUnauthorized);
    };
  }, []);

  /* ====================================================
       LOAD FILES / FOLDERS
    ==================================================== */

  async function load() {
    if (!user) {
      return;
    }

    try {
      const [filesResponse, foldersResponse] = await Promise.all([
        api.get("/files", {
          params: {
            view,
            folder_id: folder,
            q,
          },
        }),

        api.get("/folders"),
      ]);

      setFiles(filesResponse.data);

      setFolders(foldersResponse.data);
    } catch (error) {
      if (error.response?.status !== 401) {
        setToast(error.response?.data?.detail || "Unable to load files");
      }
    }
  }

  useEffect(() => {
    if (user) {
      load();
    }
  }, [user, view, folder, q]);

  /* ====================================================
       UPLOAD
    ==================================================== */

  const upload = async (accepted) => {
    for (const file of accepted) {
      const fd = new FormData();

      fd.append("file", file);

      try {
        await api.post("/files/upload", fd, {
          params: {
            folder_id: folder,
          },

          headers: {
            "Content-Type": "multipart/form-data",
          },

          onUploadProgress: (event) => {
            if (!event.total) {
              return;
            }

            const percentage = Math.round((event.loaded / event.total) * 100);

            setToast(`Uploading ${file.name} · ${percentage}%`);
          },
        });
      } catch (error) {
        setToast(error.response?.data?.detail || `Upload failed: ${file.name}`);
      }
    }

    setToast("");

    load();
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: upload,
  });

  /* ====================================================
       CREATE FOLDER
    ==================================================== */

  async function createFolder(e) {
    e.preventDefault();

    if (!newFolder.trim()) {
      return;
    }

    try {
      await api.post("/folders", {
        name: newFolder.trim(),
        parent_id: folder,
      });

      setNewFolder("");

      setShowFolder(false);

      load();
    } catch (error) {
      setToast(error.response?.data?.detail || "Unable to create folder");
    }
  }

  /* ====================================================
       GENERIC ACTION
    ==================================================== */

  async function act(promise) {
    try {
      await promise;

      await load();
    } catch (error) {
      setToast(error.response?.data?.detail || "Action failed");
    }
  }

  /* ====================================================
       LOGOUT
    ==================================================== */

  async function logout() {
    try {
      await api.post("/auth/logout");
    } catch (error) {
      console.error("Logout request failed:", error);
    } finally {
      /*
       * Clear frontend state regardless of
       * backend response.
       */

      setUser(null);

      setFolders([]);

      setFiles([]);

      setFolder(null);

      setView("drive");

      setQ("");

      setShare(null);

      setLink(null);

      setToast("");
    }
  }

  /* ====================================================
       AUTH CHECK LOADING
    ==================================================== */

  if (authChecking) {
    return (
      <div className="auth">
        <div className="auth-card">
          <div className="brand">
            <span className="logo">
              <Cloud size={22} />
            </span>

            <b>CloudDrive</b>
          </div>

          <p className="muted">Checking your session...</p>
        </div>
      </div>
    );
  }

  /* ====================================================
       AUTH SCREEN
    ==================================================== */

  if (!user) {
    return (
      <Auth
        onLogin={(loggedInUser) => {
          setUser(loggedInUser);
        }}
      />
    );
  }

  /* ====================================================
       AUTHENTICATED APPLICATION
    ==================================================== */

  return (
    <div className="app">
      <aside>
        <div className="brand">
          <span className="logo">
            <Cloud size={20} />
          </span>

          <b>CloudDrive</b>
        </div>

        <button className="upload" {...getRootProps()}>
          <input {...getInputProps()} />
          <UploadCloud size={18} />
          Upload files
        </button>

        <nav>
          {[
            ["drive", "My Drive", Cloud],
            ["shared", "Shared with me", Users],
            ["starred", "Starred", Star],
            ["trash", "Trash", Trash2],
          ].map(([id, title, Icon]) => (
            <button
              key={id}
              className={view === id ? "active" : ""}
              onClick={() => {
                setView(id);
                setFolder(null);
              }}
            >
              <Icon size={18} />

              {title}
            </button>
          ))}
        </nav>

        <div className="storage">
          <div className="storage-head">
            <span>Storage</span>

            <b>Free</b>
          </div>

          <div className="bar">
            <i />
          </div>

          <small>Vercel Blob Storage</small>
        </div>

        <div className="profile">
          <div className="avatar">{user.name?.charAt(0)?.toUpperCase()}</div>

          <div>
            <b>{user.name}</b>

            <small>{user.email}</small>
          </div>

          <button type="button" onClick={logout} title="Logout">
            <LogOut size={16} />
          </button>
        </div>
      </aside>

      <main>
        <header>
          <div className="search">
            <Search size={18} />

            <input
              placeholder="Search files"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </div>

          <div className="header-actions">
            <button
              onClick={() => setGrid(true)}
              className={grid ? "selected" : ""}
            >
              <Grid2X2 size={18} />
            </button>

            <button
              onClick={() => setGrid(false)}
              className={!grid ? "selected" : ""}
            >
              <List size={18} />
            </button>

            <div className="avatar">{user.name?.charAt(0)?.toUpperCase()}</div>
          </div>
        </header>

        <section className="content">
          <div className="title-row">
            <div>
              <div
                className="crumb"
                onClick={() => {
                  setView("drive");
                  setFolder(null);
                }}
              >
                My Drive
                {folder && (
                  <>
                    <ChevronRight size={15} />

                    {folders.find((x) => x.id === folder)?.name}
                  </>
                )}
              </div>

              <h2>
                {view === "drive"
                  ? "Files"
                  : view === "shared"
                    ? "Shared with me"
                    : view === "starred"
                      ? "Starred"
                      : "Trash"}
              </h2>
            </div>

            {view === "drive" && (
              <div className="actions">
                <button onClick={() => setShowFolder(true)}>
                  <Plus size={17} />
                  New folder
                </button>
              </div>
            )}
          </div>

          {isDragActive && (
            <div className="drop-overlay">Drop files to upload</div>
          )}

          <div className="dropzone" {...getRootProps()}>
            <input {...getInputProps()} />

            <UploadCloud size={20} />

            <span>
              Drag & drop files here or <b>browse</b>
            </span>
          </div>

          {folder === null && view === "drive" && (
            <div className="folders">
              {folders
                .filter((f) => f.parent_id === null)
                .map((f) => (
                  <button
                    className="folder-card"
                    key={f.id}
                    onDoubleClick={() => setFolder(f.id)}
                  >
                    <Folder size={24} />

                    <span>{f.name}</span>
                  </button>
                ))}
            </div>
          )}

          {files.length === 0 ? (
            <div className="empty">
              <File size={40} />

              <h3>{q ? "No matches" : "Nothing here yet"}</h3>

              <p>Upload a file to get started.</p>
            </div>
          ) : grid ? (
            <div className="file-grid">
              {files.map((file) => (
                <FileCard
                  key={file.id}
                  f={file}
                  on={act}
                  onShare={() => setShare(file)}
                />
              ))}
            </div>
          ) : (
            <div className="table">
              {files.map((file) => (
                <FileRow
                  key={file.id}
                  f={file}
                  on={act}
                  onShare={() => setShare(file)}
                />
              ))}
            </div>
          )}
        </section>
      </main>

      {showFolder && (
        <Modal title="New folder" close={() => setShowFolder(false)}>
          <form onSubmit={createFolder}>
            <input
              autoFocus
              placeholder="Folder name"
              value={newFolder}
              onChange={(e) => setNewFolder(e.target.value)}
            />

            <button className="primary full">Create folder</button>
          </form>
        </Modal>
      )}

      {share && (
        <Modal
          title={`Share “${share.name}”`}
          close={() => {
            setShare(null);
            setLink(null);
            setShareEmail("");
          }}
        >
          <p className="muted">Invite another CloudDrive user.</p>

          <input
            placeholder="Email address"
            value={shareEmail}
            onChange={(e) => setShareEmail(e.target.value)}
          />

          <button
            className="primary full"
            onClick={() =>
              act(
                api
                  .post("/shares", {
                    file_id: share.id,
                    email: shareEmail,
                    role: "viewer",
                  })
                  .then(() => {
                    setShare(null);
                    setShareEmail("");

                    setToast("Shared successfully");
                  }),
              )
            }
          >
            Share as viewer
          </button>

          <button
            className="secondary full"
            onClick={() =>
              act(
                api
                  .post("/shares", {
                    file_id: share.id,
                    email: shareEmail,
                    role: "editor",
                  })
                  .then(() => {
                    setShare(null);
                    setShareEmail("");

                    setToast("Shared successfully");
                  }),
              )
            }
          >
            Share as editor
          </button>

          <hr />

          <button
            className="secondary full"
            onClick={() =>
              api
                .post("/public-link", {
                  file_id: share.id,
                })
                .then((response) => setLink(response.data.token))
                .catch((error) =>
                  setToast(
                    error.response?.data?.detail ||
                      "Unable to create public link",
                  ),
                )
            }
          >
            <Share2 size={16} />
            Create public link
          </button>

          {link && (
            <div className="linkbox">
              {window.location.origin}
              /share/
              {link}
            </div>
          )}
        </Modal>
      )}

      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}

/* ========================================================
   FILE CARD
======================================================== */

function FileCard({ f, on, onShare }) {
  return (
    <div className="file-card">
      <div className="file-icon">
        <File size={28} />
      </div>

      <div className="file-info">
        <b title={f.name}>{f.name}</b>

        <small>
          {fmt(f.size)}
          {" · "}
          {f.mime_type || "file"}
        </small>
      </div>

      <div className="card-actions">
        <button onClick={() => on(api.post(`/files/${f.id}/star`))}>
          <Star size={16} fill={f.starred ? "currentColor" : "none"} />
        </button>

        {f.deleted_at ? (
          <button onClick={() => on(api.post(`/files/${f.id}/restore`))}>
            <RotateCcw size={16} />
          </button>
        ) : (
          <>
            <button onClick={onShare}>
              <Share2 size={16} />
            </button>

            <button onClick={() => on(api.delete(`/files/${f.id}`))}>
              <Trash2 size={16} />
            </button>

            <button
              onClick={() =>
                (window.location.href = `${api.defaults.baseURL}/files/${f.id}/download`)
              }
            >
              <Download size={16} />
            </button>
          </>
        )}
      </div>
    </div>
  );
}

/* ========================================================
   FILE ROW
======================================================== */

function FileRow({ f, on, onShare }) {
  return (
    <div className="file-row">
      <File size={20} />

      <b>{f.name}</b>

      <span>{fmt(f.size)}</span>

      <span>{f.mime_type}</span>

      <button onClick={onShare}>
        <Share2 size={16} />
      </button>

      <button onClick={() => on(api.delete(`/files/${f.id}`))}>
        <Trash2 size={16} />
      </button>

      <button
        onClick={() =>
          (window.location.href = `${api.defaults.baseURL}/files/${f.id}/download`)
        }
      >
        <Download size={16} />
      </button>
    </div>
  );
}

/* ========================================================
   MODAL
======================================================== */

function Modal({ title, close, children }) {
  return (
    <div className="modal-backdrop">
      <div className="modal">
        <div className="modal-head">
          <h3>{title}</h3>

          <button type="button" onClick={close}>
            ×
          </button>
        </div>

        {children}
      </div>
    </div>
  );
}

/* ========================================================
   START APPLICATION
======================================================== */

createRoot(document.getElementById("root")).render(<App />);
