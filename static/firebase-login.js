
import { initializeApp } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-app.js";
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-auth.js";


const firebaseConfig = {
    apiKey: "AIzaSyBMoMIJMqCIJZDgxEDpUShZCS2o1Ew_nxs",
    authDomain: "assignment---1-1e153.firebaseapp.com",
    projectId: "assignment---1-1e153",
    storageBucket: "assignment---1-1e153.appspot.com",
    messagingSenderId: "133737118405",
    appId: "1:133737118405:web:244db60467492f4f10ceac"
};
window.addEventListener("load", function() {
    const app = initializeApp(firebaseConfig);
    const auth = getAuth(app);

    updateUI(document.cookie);
    console.log("Firebase App Initialized");

    
    document.getElementById("sign-up").addEventListener('click', function() {
        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value.trim();

        createUserWithEmailAndPassword(auth, email, password)
        .then((userCredential) => {
            const user = userCredential.user;
            console.log("User Created:", user);

            user.getIdToken().then((token) => {
                document.cookie = `token=${token}; path=/; SameSite=Strict`;
                console.log("Signup Token Set:", document.cookie);
                window.location = "/";
            });
        })
        .catch((error) => {
            console.error("Signup Error:", error.code, error.message);
        });
    });

    
    document.getElementById("login").addEventListener('click', function() {
        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value.trim();

        signInWithEmailAndPassword(auth, email, password)
        .then((userCredential) => {
            const user = userCredential.user;
            console.log("User Logged In:", user);

            user.getIdToken().then((token) => {
                document.cookie = `token=${token}; path=/; SameSite=Strict`;
                console.log("Login Token Set:", document.cookie);
                window.location = "/";
            });
        })
        .catch((error) => {
            console.error("Login Error:", error.code, error.message);
        });
    });

    
    document.getElementById("sign-out").addEventListener('click', function() {
        signOut(auth)
        .then(() => {
            document.cookie = "token=; path=/; SameSite=Strict"; 
            console.log("User Signed Out");
            window.location = "/";
        })
        .catch((error) => {
            console.error("Logout Error:", error.code, error.message);
        });
    });
});


function updateUI(cookie) {
    const token = parseCookieToken(cookie);

    if (token.length > 0) {
        document.getElementById("login-box").hidden = true;
        document.getElementById("sign-out").hidden = false;
    } else {
        document.getElementById("login-box").hidden = false;
        document.getElementById("sign-out").hidden = true;
    }
}


function parseCookieToken(cookie) {
    const strings = cookie.split(';');
    for (let i = 0; i < strings.length; i++) {
        const temp = strings[i].split('=');
        if (temp[0].trim() === "token") { 
            return temp[1];
        }
    }
    return "";
}