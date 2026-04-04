from __future__ import annotations

from textual.app import App
from textual.widgets import Button, TextInput, Label

class AIApp(App):
    """Main SPIDER application with AI integration."""

    TITLE = "SPIDER - Security AI"
    CSS = """# AI screen styles
.ai-screen {
    background: #0a0a0a;
}

.ai-input {
    background: #141414;
    border: thick #2a2a2a;
}

.ai-output {
    background: #0d0d0d;
    border: thick #4a4a2a;
}
"""

    def __init__(self, model_path: str) -> None:
        super().__init__()
        self.model_path = model_path
        self.ai_output = """
        AI Security Analysis
        -------------------
        Loading model...
        """

    def on_mount(self) -> None:
        """Initialize application."""
        self.push_screen(AIHomeScreen(self))

class AIHomeScreen:
    """Home screen for AI integration."""

    def __init__(self, app: AIApp) -> None:
        self.app = app
        self.model_list = ["ollama", "lm-studio"]

    def render(self) -> str:
        return f"""<div class='ai-screen'>
            <div class='ai-header'>
                <h1>SPIDER AI Security</h1>
                <p>Choose your AI model:</p>
            </div>
            <div class='ai-input'>
                <input type='text' placeholder='Select model (ollama/lm-studio)'/>
            </div>
            <div class='ai-output'>
                {self.app.ai_output}
            </div>
        </div>"""

    def on_button_click(self, button: Button) -> None:
        if button.text == "Load Model":
            self.app.ai_output = """
            AI Security Analysis
            -------------------
            Loading {button.text} model...
            """
            self.app.push_screen(AIAnalysisScreen(self.app))

class AIAnalysisScreen:
    """Analysis screen for AI security checks."""

    def __init__(self, home_screen: AIHomeScreen) -> None:
        self.home_screen = home_screen
        self.analysis_results = """
        Security Analysis Results
        ------------------------
        Running AI analysis...
        """

    def render(self) -> str:
        return f"""<div class='ai-screen'>
            <div class='ai-header'>
                <h1>Security Analysis</h1>
                <p>Running AI security scan...</p>
            </div>
            <div class='ai-output'>
                {self.analysis_results}
            </div>
        </div>"""

    def on_scan(self) -> None:
        self.analysis_results = """
        Security Analysis Results
        ------------------------
        Scanning for vulnerabilities...
        """
        self.app.push_screen(AIResultsScreen(self))

class AIResultsScreen:
    """Results screen for AI security checks."""

    def __init__(self, analysis_screen: AIAnalysisScreen) -> None:
        self.analysis_screen = analysis_screen
        self.risk_score = 85
        self.recommendations = ["Update dependencies", "Patch CVE-2023-12345"]

    def render(self) -> str:
        return f"""<div class='ai-screen'>
            <div class='ai-header'>
                <h1>Security Scan Results</h1>
                <p>Risk Score: {self.risk_score}/100</p>
            </div>
            <div class='ai-output'>
                <h2>Recommendations:</h2>
                <ul>
                    {''.join([f'<li>{item}</li>' for item in self.recommendations])}
                </ul>
            </div>
        </div>"""

    def on_close(self) -> None:
        self.app.push_screen(self.home_screen)

if __name__ == "__main__":
    app = AIApp("ollama")
    app.run()
    "