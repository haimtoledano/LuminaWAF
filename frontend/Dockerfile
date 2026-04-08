# Use an official Node.js runtime as a parent image
FROM node:20

# Set the working directory in the container to /app
WORKDIR /app

# Copy package.json and package-lock.json (if exists) into the container at /app
COPY package*.json ./

# Install any needed packages specified in package.json
RUN npm install

# Bundle app source inside Docker image
COPY . .

# Make port 5173 available to the world outside this container
EXPOSE 5173

# Command to run your app using Vite
CMD ["npm", "run", "dev", "--", "--host"]
