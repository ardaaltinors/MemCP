from typing import Callable, Awaitable


class MCPOAuthRedirectMiddleware:
    """
    Middleware to handle OAuth callback redirects to custom URL schemes (e.g., cursor://).

    Browsers block HTTP 302 redirects to custom URL schemes for security reasons.
    This middleware intercepts redirects to custom schemes and returns an HTML page
    with JavaScript that can trigger the custom URL scheme.
    """

    def __init__(self, app: Callable[[dict, Callable, Callable], Awaitable[None]]):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            return await self.app(scope, receive, send)

        path: str = scope.get("path", "")

        if not path.startswith("/auth/callback"):
            return await self.app(scope, receive, send)

        async def send_wrapper(message):
            if message.get("type") == "http.response.start":
                status = message.get("status")
                headers = message.get("headers", [])

                if status == 302:
                    location = None
                    for name, value in headers:
                        if name.lower() == b"location":
                            location = value.decode()
                            break

                    if location and (location.startswith("cursor://") or location.startswith("vscode://")):
                        html_content = self._create_redirect_page(location)
                        html_bytes = html_content.encode('utf-8')

                        await send({
                            "type": "http.response.start",
                            "status": 200,
                            "headers": [
                                (b"content-type", b"text/html; charset=utf-8"),
                                (b"content-length", str(len(html_bytes)).encode()),
                                (b"cache-control", b"no-store"),
                            ],
                        })
                        await send({
                            "type": "http.response.body",
                            "body": html_bytes,
                        })
                        return

            await send(message)

        await self.app(scope, receive, send_wrapper)

    def _create_redirect_page(self, redirect_url: str) -> str:
        """Create an HTML page that redirects using JavaScript."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Authorization Successful</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            background: white;
            padding: 3rem;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 500px;
            text-align: center;
        }}
        h1 {{
            color: #2d3748;
            margin-bottom: 1rem;
            font-size: 1.875rem;
        }}
        p {{
            color: #4a5568;
            line-height: 1.6;
            margin-bottom: 1.5rem;
        }}
        .spinner {{
            border: 3px solid #f3f4f6;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 2rem auto;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        .manual-link {{
            display: none;
            margin-top: 2rem;
            padding: 1rem;
            background: #f7fafc;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }}
        .manual-link code {{
            display: block;
            margin: 1rem 0;
            padding: 0.75rem;
            background: white;
            border: 1px solid #cbd5e0;
            border-radius: 4px;
            font-size: 0.875rem;
            word-break: break-all;
            color: #2d3748;
        }}
        .copy-btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1rem;
            transition: background 0.2s;
        }}
        .copy-btn:hover {{
            background: #5a67d8;
        }}
        .success-icon {{
            font-size: 3rem;
            margin-bottom: 1rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="success-icon">✓</div>
        <h1>Authorization Successful!</h1>
        <p>Redirecting you back to the application...</p>
        <div class="spinner"></div>

        <div class="manual-link" id="manualLink">
            <p><strong>The automatic redirect didn't work?</strong></p>
            <p>Click the button below to copy the redirect URL and paste it into your browser's address bar:</p>
            <code id="redirectUrl">{redirect_url}</code>
            <button class="copy-btn" onclick="copyUrl()">Copy URL</button>
        </div>
    </div>

    <script>
        const redirectUrl = {repr(redirect_url)};

        function copyUrl() {{
            navigator.clipboard.writeText(redirectUrl).then(() => {{
                const btn = document.querySelector('.copy-btn');
                btn.textContent = 'Copied!';
                setTimeout(() => {{
                    btn.textContent = 'Copy URL';
                }}, 2000);
            }});
        }}

        function attemptRedirect() {{
            try {{
                window.location.href = redirectUrl;
            }} catch (e) {{
                console.error('Redirect failed:', e);
                showManualLink();
            }}
        }}

        function showManualLink() {{
            document.querySelector('.spinner').style.display = 'none';
            document.getElementById('manualLink').style.display = 'block';
        }}

        setTimeout(attemptRedirect, 500);

        setTimeout(showManualLink, 5000);
    </script>
</body>
</html>"""
