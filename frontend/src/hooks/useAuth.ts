import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { useCallback, useEffect, useState } from "react"

import { type UserPublic, UsersService } from "@/client"
import { supabase } from "@/lib/supabase"
import useCustomToast from "./useCustomToast"

interface LoginCredentials {
  email: string
  password: string
}

const isLoggedIn = () => {
  // Check synchronously via localStorage (Supabase persists session there)
  const storageKey = `sb-${import.meta.env.VITE_SUPABASE_URL?.split("//")[1]?.split(".")[0]}-auth-token`
  return localStorage.getItem(storageKey) !== null
}

const useAuth = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showErrorToast } = useCustomToast()
  const [isReady, setIsReady] = useState(false)

  // Listen for Supabase auth state changes
  useEffect(() => {
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event) => {
      setIsReady(true)
      if (event === "SIGNED_OUT") {
        queryClient.clear()
      }
      if (event === "SIGNED_IN" || event === "TOKEN_REFRESHED") {
        queryClient.invalidateQueries({ queryKey: ["currentUser"] })
      }
    })

    return () => subscription.unsubscribe()
  }, [queryClient])

  const { data: user } = useQuery<UserPublic | null, Error>({
    queryKey: ["currentUser"],
    queryFn: UsersService.readUserMe,
    enabled: isLoggedIn(),
  })

  const login = async (credentials: LoginCredentials) => {
    const { error } = await supabase.auth.signInWithPassword({
      email: credentials.email,
      password: credentials.password,
    })
    if (error) {
      throw new Error(error.message)
    }
  }

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      navigate({ to: "/" })
    },
    onError: (error: Error) => {
      showErrorToast(error.message)
    },
  })

  const logout = useCallback(async () => {
    await supabase.auth.signOut()
    navigate({ to: "/login" })
  }, [navigate])

  return {
    loginMutation,
    logout,
    user,
    isReady,
  }
}

export { isLoggedIn }
export default useAuth
