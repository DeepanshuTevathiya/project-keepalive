const DEFAULT_REPOSITORY = "DeepanshuTevathiya/project-keepalive";
const FILE_PATH = "projects.json";
const BRANCH = process.env.GITHUB_BRANCH || "main";

function githubHeaders() {
  if (!process.env.GITHUB_TOKEN) throw new Error("GITHUB_TOKEN is not configured.");
  return { Accept: "application/vnd.github+json", Authorization: `Bearer ${process.env.GITHUB_TOKEN}`, "X-GitHub-Api-Version": "2022-11-28" };
}
function repository() { return process.env.GITHUB_REPO || DEFAULT_REPOSITORY; }
function authorized(request) { return Boolean(process.env.ADMIN_KEY) && request.headers["x-admin-key"] === process.env.ADMIN_KEY; }

async function getProjects() {
  const response = await fetch(`https://api.github.com/repos/${repository()}/contents/${FILE_PATH}?ref=${encodeURIComponent(BRANCH)}`, { headers: githubHeaders() });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || "GitHub could not read projects.json.");
  const projects = JSON.parse(Buffer.from(data.content, "base64").toString("utf8"));
  if (!Array.isArray(projects)) throw new Error("projects.json must contain a list.");
  return { projects, sha: data.sha };
}

function validateProject(project) {
  if (!project || typeof project !== "object") return "Project must be an object.";
  if (!project.name || typeof project.name !== "string") return "A project name is required.";
  if (!project.url || typeof project.url !== "string") return "A project URL is required.";
  try { const url = new URL(project.url); if (!["http:", "https:"].includes(url.protocol)) return "URL must use HTTP or HTTPS."; } catch { return "Enter a valid project URL."; }
  if (!["streamlit", "huggingface"].includes(project.type)) return "Choose Streamlit or Hugging Face.";
  return null;
}

module.exports = async function handler(request, response) {
  try {
    if (!authorized(request)) return response.status(401).json({ error: "Invalid admin key." });
    if (request.method === "GET") { const { projects } = await getProjects(); return response.status(200).json({ projects }); }
    if (request.method !== "POST") return response.status(405).json({ error: "Method not allowed." });
    const project = { name: String(request.body?.name || "").trim(), url: String(request.body?.url || "").trim(), type: request.body?.type };
    const validationError = validateProject(project);
    if (validationError) return response.status(400).json({ error: validationError });
    const current = await getProjects();
    if (current.projects.some((item) => item.name.toLowerCase() === project.name.toLowerCase())) return response.status(409).json({ error: "A project with that name already exists." });
    const projects = [...current.projects, project];
    const update = await fetch(`https://api.github.com/repos/${repository()}/contents/${FILE_PATH}`, { method: "PUT", headers: { ...githubHeaders(), "Content-Type": "application/json" }, body: JSON.stringify({ message: `Add ${project.name} to keepalive projects`, content: Buffer.from(`${JSON.stringify(projects, null, 2)}\n`).toString("base64"), sha: current.sha, branch: BRANCH }) });
    const result = await update.json();
    if (!update.ok) throw new Error(result.message || "GitHub could not update projects.json.");
    return response.status(201).json({ projects });
  } catch (error) { return response.status(500).json({ error: error.message || "Unexpected server error." }); }
};
