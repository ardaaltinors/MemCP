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
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Authorization Successful - MemCP</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background-color: #0D0D1A;
            background-image:
                radial-gradient(ellipse 800px 600px at 10% 90%, rgba(59, 130, 246, 0.15) 0%, rgba(99, 102, 241, 0.1) 40%, transparent 70%),
                radial-gradient(circle 1000px at 50% 50%, rgba(139, 92, 246, 0.08) 0%, transparent 60%),
                radial-gradient(ellipse 900px 700px at 85% 15%, rgba(168, 85, 247, 0.12) 0%, rgba(139, 92, 246, 0.06) 50%, transparent 70%),
                radial-gradient(circle 600px at 30% 30%, rgba(59, 130, 246, 0.05) 0%, transparent 50%);
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-size: cover;
            color: #ffffff;
        }}

        .container {{
            background: rgba(17, 24, 39, 0.5);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 3rem;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 520px;
            width: 90%;
            text-align: center;
        }}

        .branding {{
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 2rem;
            gap: 0.75rem;
        }}

        .logo {{
            width: 48px;
            height: 48px;
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 1.5rem;
            color: white;
            box-shadow: 0 0 30px rgba(59, 130, 246, 0.3);
        }}

        .brand-name {{
            font-size: 1.75rem;
            font-weight: 700;
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .success-icon {{
            width: 80px;
            height: 80px;
            margin: 0 auto 1.5rem;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.5rem;
            animation: success-pulse 2s ease-in-out infinite;
            box-shadow: 0 0 30px rgba(16, 185, 129, 0.4);
        }}

        @keyframes success-pulse {{
            0%, 100% {{
                box-shadow: 0 0 30px rgba(16, 185, 129, 0.4);
                transform: scale(1);
            }}
            50% {{
                box-shadow: 0 0 50px rgba(16, 185, 129, 0.6);
                transform: scale(1.05);
            }}
        }}

        h1 {{
            color: #ffffff;
            margin-bottom: 0.75rem;
            font-size: 1.875rem;
            font-weight: 700;
        }}

        p {{
            color: #9ca3af;
            line-height: 1.6;
            margin-bottom: 1.5rem;
            font-size: 1rem;
        }}

        .spinner {{
            border: 3px solid rgba(59, 130, 246, 0.2);
            border-top: 3px solid #3b82f6;
            border-radius: 50%;
            width: 48px;
            height: 48px;
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
            padding: 1.5rem;
            background: rgba(17, 24, 39, 0.6);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.06);
        }}

        .manual-link p {{
            color: #9ca3af;
            margin-bottom: 1rem;
        }}

        .manual-link strong {{
            color: #ffffff;
            display: block;
            margin-bottom: 0.5rem;
        }}

        .manual-link code {{
            display: block;
            margin: 1rem 0;
            padding: 1rem;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            font-size: 0.875rem;
            word-break: break-all;
            color: #e5e7eb;
            font-family: 'JetBrains Mono', 'Courier New', monospace;
            text-align: left;
        }}

        .copy-btn {{
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            color: white;
            border: none;
            padding: 0.875rem 2rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        }}

        .copy-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
        }}

        .copy-btn:active {{
            transform: translateY(0);
        }}

        @media (max-width: 640px) {{
            .container {{
                padding: 2rem 1.5rem;
            }}

            h1 {{
                font-size: 1.5rem;
            }}

            .brand-name {{
                font-size: 1.5rem;
            }}

            .logo {{
                width: 40px;
                height: 40px;
                font-size: 1.25rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="branding">
            <div class="logo">M</div>
            <div class="brand-name">MemCP</div>
        </div>

        <div class="success-icon">✓</div>
        <h1>Authorization Successful!</h1>
        <p>Redirecting you back to the application...</p>
        <div class="spinner"></div>

        <div class="manual-link" id="manualLink">
            <strong>The automatic redirect didn't work?</strong>
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
                const originalText = btn.textContent;
                btn.textContent = 'Copied!';
                btn.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
                setTimeout(() => {{
                    btn.textContent = originalText;
                    btn.style.background = 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)';
                }}, 2000);
            }}).catch(err => {{
                console.error('Failed to copy:', err);
                alert('Failed to copy URL. Please copy it manually.');
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
            const spinner = document.querySelector('.spinner');
            const manualLink = document.getElementById('manualLink');
            if (spinner) spinner.style.display = 'none';
            if (manualLink) manualLink.style.display = 'block';
        }}

        setTimeout(attemptRedirect, 500);
        setTimeout(showManualLink, 5000);
    </script>
</body>
</html>"""
