<template>
  <div class="container">
    <h1>Quizio 快問快答</h1>
    <router-view></router-view>
  </div>
</template>

<style>
/* Global shared styles for all views */
.container {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  max-width: 800px;
  margin: 40px auto;
  padding: 0 20px;
  text-align: center;
}
h1 {
  color: #2c3e50;
  margin-bottom: 30px;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  text-align: left;
  margin: 0 auto;
}

.btn-primary {
  background-color: #3498db;
  color: white;
  border: none;
  padding: 14px;
  font-size: 16px;
  font-weight: bold;
  border-radius: 8px;
  cursor: pointer;
  transition: 0.3s;
  width: 100%;
}
.btn-primary:hover:not(:disabled) {
  background-color: #2980b9;
}
.btn-primary:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: #2ecc71;
  color: white;
  border: none;
  padding: 14px;
  font-size: 16px;
  font-weight: bold;
  border-radius: 8px;
  cursor: pointer;
  transition: 0.3s;
  width: 100%;
}
.btn-secondary:hover {
  background-color: #27ae60;
}

.btn-danger {
  background-color: #e74c3c;
  color: white;
  border: none;
  padding: 14px;
  font-size: 16px;
  font-weight: bold;
  border-radius: 8px;
  cursor: pointer;
  transition: 0.3s;
  width: 100%;
  margin-top: 20px;
}
.btn-danger:hover {
  background-color: #c0392b;
}

.error-msg {
  color: #e74c3c;
  margin-top: 15px;
  text-align: center;
  font-weight: bold;
}
</style>
