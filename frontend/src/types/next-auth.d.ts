declare module 'next-auth' {
  interface Session {
    user: {
      id: string
      email: string
      name?: string | null
      image?: string | null
      oauth_provider?: string | null
      is_admin: boolean
      new_user?: boolean
    }
    provider?: string
  }

  interface User {
    backendUser?: {
      id: string
      email: string
      name?: string | null
      oauth_provider?: string | null
      is_admin: boolean
      new_user?: boolean
    }
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    backendUser?: {
      id: string
      email: string
      name?: string | null
      oauth_provider?: string | null
      is_admin: boolean
      new_user?: boolean
    }
    provider?: string
    accessToken?: string
    refreshToken?: string
    expiresAt?: number
  }
}