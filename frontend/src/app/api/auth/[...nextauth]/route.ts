import NextAuth from 'next-auth'
import GoogleProvider from 'next-auth/providers/google'
import { api } from '@/lib/api'

const handler = NextAuth({
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      authorization: {
        params: {
          prompt: 'consent',
          access_type: 'offline',
          response_type: 'code',
          scope: 'openid email profile',
        },
      },
    }),
  ],

  callbacks: {
    async signIn({ user, account, profile }) {
      try {
        console.log('OAuth sign-in attempt:', { user: user.email, provider: account?.provider })

        if (!account || !user.email) {
          console.error('Missing account or user email')
          return false
        }

        // Prepare OAuth data for backend
        const oauthData = {
          provider_user_id: account.providerAccountId,
          email: user.email,
          name: user.name,
          avatar_url: user.image,
          access_token: account.access_token,
          refresh_token: account.refresh_token,
          token_expires_at: account.expires_at ? new Date(account.expires_at * 1000).toISOString() : null,
          provider_data: {
            given_name: (profile as any)?.given_name,
            family_name: (profile as any)?.family_name,
            locale: (profile as any)?.locale,
            verified_email: (profile as any)?.email_verified,
          },
        }

        console.log('Sending OAuth data to backend:', { email: oauthData.email, provider: account.provider })

        // Call backend OAuth endpoint
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/oauth/signin`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(oauthData),
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}))
          console.error('Backend OAuth error:', response.status, errorData)
          return false
        }

        const backendData = await response.json()
        console.log('Backend OAuth success:', { email: backendData.user.email, new_user: backendData.user.new_user })

        // Store backend token for API calls
        if (backendData.access_token) {
          api.setToken(backendData.access_token)
        }

        // Add backend user info to session
        user.backendUser = {
          id: backendData.user.id,
          email: backendData.user.email,
          name: backendData.user.name,
          oauth_provider: backendData.user.oauth_provider,
          is_admin: backendData.user.is_admin,
          new_user: backendData.user.new_user,
        }

        return true
      } catch (error) {
        console.error('OAuth sign-in error:', error)
        return false
      }
    },

    async jwt({ token, user, account }) {
      // Persist backend user info and OAuth tokens to JWT
      if (user && account) {
        token.backendUser = user.backendUser
        token.provider = account.provider
        token.accessToken = account.access_token
        token.refreshToken = account.refresh_token
        token.expiresAt = account.expires_at
      }
      return token
    },

    async session({ session, token }) {
      // Send backend user info and OAuth tokens to client
      if (token.backendUser) {
        session.user = {
          ...session.user,
          ...token.backendUser,
        }
      }

      // Add OAuth provider info
      if (token.provider) {
        session.provider = token.provider
      }

      return session
    },

    async redirect({ url, baseUrl }) {
      // Allows relative callback URLs
      if (url.startsWith('/')) return `${baseUrl}${url}`
      // Allows callback URLs on the same origin
      else if (new URL(url).origin === baseUrl) return url
      return baseUrl
    },
  },

  pages: {
    signIn: '/login',
    error: '/login',
  },

  session: {
    strategy: 'jwt',
    maxAge: 24 * 60 * 60, // 24 hours
  },

  jwt: {
    maxAge: 24 * 60 * 60, // 24 hours
  },

  debug: process.env.NODE_ENV === 'development',
})

export { handler as GET, handler as POST }