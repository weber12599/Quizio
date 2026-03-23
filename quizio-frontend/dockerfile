# Use the official Node image
FROM node:20-slim

# Set working directory
WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy frontend source code
COPY . .

# Expose Vite default port
EXPOSE 5173

# Start Vite dev server and expose it to the network
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]