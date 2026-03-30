import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

export default defineNuxtPlugin(() => {
  const router = useRouter()

  // Configure NProgress
  NProgress.configure({
    showSpinner: false,
    speed: 200,
    minimum: 0.1
  })

  router.beforeEach(() => {
    NProgress.start()
  })

  router.afterEach(() => {
    NProgress.done()
  })
})
