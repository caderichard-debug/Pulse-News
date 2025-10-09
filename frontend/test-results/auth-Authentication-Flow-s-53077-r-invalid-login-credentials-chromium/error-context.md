# Page snapshot

```yaml
- generic [ref=e1]:
  - generic [ref=e3]:
    - generic [ref=e4]:
      - heading "⚡ Pulse" [level=1] [ref=e5]
      - paragraph [ref=e6]: Welcome back
    - generic [ref=e7]:
      - generic [ref=e8]:
        - generic [ref=e9]: Email
        - textbox "Email" [ref=e10]:
          - /placeholder: john@example.com
          - text: nonexistent@example.com
      - generic [ref=e11]:
        - generic [ref=e12]: Password
        - textbox "Password" [active] [ref=e13]:
          - /placeholder: ••••••••
          - text: WrongPassword123!
      - button "Log In" [ref=e14]
    - generic [ref=e15]:
      - text: Don't have an account?
      - link "Sign up" [ref=e16] [cursor=pointer]:
        - /url: /signup
  - button "Open Next.js Dev Tools" [ref=e22] [cursor=pointer]:
    - img [ref=e23]
  - alert [ref=e26]
```