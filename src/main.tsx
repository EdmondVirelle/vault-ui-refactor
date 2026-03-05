import { createRoot } from "react-dom/client";
import AppShell from "./app/AppShell";
import "./index.css";

const root = createRoot(document.getElementById("root")!);
root.render(<AppShell />);
