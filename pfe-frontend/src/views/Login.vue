<template>
  <div class="flex min-h-screen items-center justify-center bg-background">
    <div class="w-full max-w-md px-6">
      
      <div class="flex flex-col items-center gap-2 mb-10">
        <SellynxLogo />
        <h1 class="text-2xl font-semibold mt-4">
          Sign in to Xtra
        </h1>
        <p class="text-sm text-gray-500">
          Access your cross-selling insights platform
        </p>
      </div>

      <form @submit.prevent="handleSubmit" class="space-y-5">

        <div class="space-y-1.5">
          <label>Email address</label>
          <input
            type="email"
            placeholder="you@company.com"
            v-model="email"
            class="h-11 w-full border rounded-md px-3"
          />
        </div>

        <div class="space-y-1.5">
          <label>Password</label>
          <input
            type="password"
            placeholder="••••••••"
            v-model="password"
            class="h-11 w-full border rounded-md px-3"
          />
        </div>

        <div class="flex items-center gap-2">
          <input type="checkbox" v-model="remember" />
          <label class="text-sm text-gray-500">
            Remember me
          </label>
        </div>

        <button
          type="submit"
          class="w-full h-11 bg-black text-white rounded-md"
        >
          Sign in
        </button>

      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import SellynxLogo from "@/components/SellynxLogo.vue";

const email = ref("");
const password = ref("");
const remember = ref(false);

const handleSubmit = () => {
  console.log(email.value, password.value, remember.value);
};
</script>