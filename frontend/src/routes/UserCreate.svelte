<script>
    import { push } from 'svelte-spa-router'
    import fastapi from "../lib/api"
    import Error from "../components/Error.svelte"

    let error = {detail:[]}
    let username = ''
    let gender = ''
    let birthdate = ''
    let email = ''
    let password1 = ''
    let password2 = ''
    let hr = 1

    function post_user(event) {
        event.preventDefault()
        let url = "/api/user/create"
        let params = {
            username: username,
            gender: gender,
            birthdate: birthdate,
            email: email,
            password1: password1,
            password2: password2,
            hr: hr
        }
        fastapi('post', url, params, 
            (json) => {
                push('/user-login')
            },
            (json_error) => {
                error = json_error
            }
        )
    }
</script>

<div class="container">
    <h5 class="my-3 border-bottom pb-2">회원 가입</h5>
    <Error error={error} />
    <form method="post">
        <div class="mb-3">
            <label for="username">사용자 이름</label>
            <input type="text" class="form-control" id="username" bind:value="{username}">
        </div>
        <div class="mb-3">
            <label for="gender">성별</label>
            <input type="text" class="form-control" id="gender" bind:value="{gender}">
        </div>
        <div class="mb-3">
            <label for="birthdate">생년월일</label>
            <input type="text" class="form-control" id="birthdate" bind:value="{birthdate}">
        </div>
        <div class="mb-3">
            <label for="email">이메일</label>
            <input type="text" class="form-control" id="email" bind:value="{email}">
        </div>
        <div class="mb-3">
            <label for="password1">비밀번호</label>
            <input type="password" class="form-control" id="password1" bind:value="{password1}">
        </div>
        <div class="mb-3">
            <label for="password2">비밀번호 확인</label>
            <input type="password" class="form-control" id="password2" bind:value="{password2}">
        </div>
        <button type="submit" class="btn btn-primary" on:click="{post_user}">생성하기</button>
    </form>
</div>