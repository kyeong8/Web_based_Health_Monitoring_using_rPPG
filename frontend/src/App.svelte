<script>
  import Router from 'svelte-spa-router'
  import Navigation from "./components/Navigation.svelte"
  import UserCreate from "./routes/UserCreate.svelte"
  import UserLogin from "./routes/UserLogin.svelte"
  import Rppg from "./routes/Rppg.svelte"


  const routes = {
    '/': UserLogin,
    '/user-create': UserCreate,
    '/user-login': UserLogin,
    '/rppg' : Rppg,
  }
</script>

<Navigation />
<Router {routes}/>