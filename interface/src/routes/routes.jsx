// Simple routing configuration
// This file can be used to define routes and paths for future use
// Currently showing the Home component as the main route

import { Home } from '../pages';

// Route definitions - can be expanded when react-router-dom is installed
export const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    exact: true
  }
  // Add more routes here as needed
  // {
  //   path: '/about',
  //   name: 'About',
  //   component: About
  // }
];

// Simple router component (without react-router-dom)
const SimpleRouter = () => {
  // For now, just return the Home component
  // This can be expanded with proper routing logic later
  return <Home />;
};

export default SimpleRouter;
