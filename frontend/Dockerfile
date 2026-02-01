
FROM node:20-alpine

WORKDIR /app

# Install dependencies based on the preferred package manager
COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

# Run in dev mode
# RUN npm run build

# Expose the port
EXPOSE 3000

# Start the application
CMD ["npm", "run", "dev"]
