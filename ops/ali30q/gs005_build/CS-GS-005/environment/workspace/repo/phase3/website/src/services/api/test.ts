/**
 * API Integration Test Suite
 *
 * Run these tests to verify API integration is working correctly
 */

import { authApi, tasksApi, agentsApi, usersApi } from './index';

/**
 * Test Configuration
 */
const TEST_CONFIG = {
  baseUrl: 'http://43.160.239.61:8000',
  testUser: {
    email: 'test@example.com',
    password: 'test123456',
    username: 'testuser',
  },
};

/**
 * Test Authentication
 */
export const testAuth = async () => {
  console.log('Testing Authentication...');

  try {
    // Test Registration
    console.log('1. Testing registration...');
    const registerResult = await authApi.register({
      email: TEST_CONFIG.testUser.email,
      password: TEST_CONFIG.testUser.password,
      username: TEST_CONFIG.testUser.username,
    });
    console.log('✓ Registration successful:', registerResult.user.username);

    // Test Login
    console.log('2. Testing login...');
    const loginResult = await authApi.login({
      email: TEST_CONFIG.testUser.email,
      password: TEST_CONFIG.testUser.password,
    });
    console.log('✓ Login successful:', loginResult.user.username);

    // Test Get Profile
    console.log('3. Testing get profile...');
    const profile = await authApi.getProfile();
    console.log('✓ Profile retrieved:', profile.username);

    // Test Token Verification
    console.log('4. Testing token verification...');
    const isValid = await authApi.verifyToken();
    console.log('✓ Token is valid:', isValid);

    // Test Logout
    console.log('5. Testing logout...');
    await authApi.logout();
    console.log('✓ Logout successful');

    console.log('✓ All authentication tests passed!\n');
    return true;
  } catch (error) {
    console.error('✗ Authentication test failed:', error);
    return false;
  }
};

/**
 * Test Tasks API
 */
export const testTasks = async () => {
  console.log('Testing Tasks API...');

  try {
    // Login first
    await authApi.login({
      email: TEST_CONFIG.testUser.email,
      password: TEST_CONFIG.testUser.password,
    });

    // Test Get Tasks
    console.log('1. Testing get tasks...');
    const tasks = await tasksApi.getTasks({ page: 1, limit: 10 });
    console.log('✓ Tasks retrieved:', tasks.items.length, 'tasks');

    // Test Create Task
    console.log('2. Testing create task...');
    const newTask = await tasksApi.createTask({
      title: 'Test Task',
      description: 'This is a test task',
      type: 'data_collection',
      reward: 100,
    });
    console.log('✓ Task created:', newTask.id);

    // Test Get Task by ID
    console.log('3. Testing get task by ID...');
    const task = await tasksApi.getTaskById(newTask.id);
    console.log('✓ Task retrieved:', task.title);

    // Test Update Task
    console.log('4. Testing update task...');
    const updatedTask = await tasksApi.updateTask(newTask.id, {
      title: 'Updated Test Task',
    });
    console.log('✓ Task updated:', updatedTask.title);

    // Test Get Available Tasks
    console.log('5. Testing get available tasks...');
    const availableTasks = await tasksApi.getAvailableTasks();
    console.log('✓ Available tasks retrieved:', availableTasks.items.length);

    // Test Delete Task
    console.log('6. Testing delete task...');
    await tasksApi.deleteTask(newTask.id);
    console.log('✓ Task deleted');

    console.log('✓ All tasks tests passed!\n');
    return true;
  } catch (error) {
    console.error('✗ Tasks test failed:', error);
    return false;
  }
};

/**
 * Test Agents API
 */
export const testAgents = async () => {
  console.log('Testing Agents API...');

  try {
    // Login first
    await authApi.login({
      email: TEST_CONFIG.testUser.email,
      password: TEST_CONFIG.testUser.password,
    });

    // Test Get Agents
    console.log('1. Testing get agents...');
    const agents = await agentsApi.getAgents({ page: 1, limit: 10 });
    console.log('✓ Agents retrieved:', agents.items.length, 'agents');

    // Test Create Agent
    console.log('2. Testing create agent...');
    const newAgent = await agentsApi.createAgent({
      name: 'Test Agent',
      type: 'worker',
      capabilities: ['data_collection', 'annotation'],
    });
    console.log('✓ Agent created:', newAgent.id);

    // Test Get Agent by ID
    console.log('3. Testing get agent by ID...');
    const agent = await agentsApi.getAgentById(newAgent.id);
    console.log('✓ Agent retrieved:', agent.name);

    // Test Update Agent
    console.log('4. Testing update agent...');
    const updatedAgent = await agentsApi.updateAgent(newAgent.id, {
      name: 'Updated Test Agent',
    });
    console.log('✓ Agent updated:', updatedAgent.name);

    // Test Get My Agents
    console.log('5. Testing get my agents...');
    const myAgents = await agentsApi.getMyAgents();
    console.log('✓ My agents retrieved:', myAgents.items.length);

    // Test Start Agent
    console.log('6. Testing start agent...');
    const startedAgent = await agentsApi.startAgent(newAgent.id);
    console.log('✓ Agent started:', startedAgent.status);

    // Test Stop Agent
    console.log('7. Testing stop agent...');
    const stoppedAgent = await agentsApi.stopAgent(newAgent.id);
    console.log('✓ Agent stopped:', stoppedAgent.status);

    // Test Delete Agent
    console.log('8. Testing delete agent...');
    await agentsApi.deleteAgent(newAgent.id);
    console.log('✓ Agent deleted');

    console.log('✓ All agents tests passed!\n');
    return true;
  } catch (error) {
    console.error('✗ Agents test failed:', error);
    return false;
  }
};

/**
 * Test Users API
 */
export const testUsers = async () => {
  console.log('Testing Users API...');

  try {
    // Login first
    await authApi.login({
      email: TEST_CONFIG.testUser.email,
      password: TEST_CONFIG.testUser.password,
    });

    // Test Get Profile
    console.log('1. Testing get profile...');
    const profile = await usersApi.getProfile();
    console.log('✓ Profile retrieved:', profile.username);

    // Test Update Profile
    console.log('2. Testing update profile...');
    const updatedProfile = await usersApi.updateProfile({
      username: 'updatedtestuser',
    });
    console.log('✓ Profile updated:', updatedProfile.username);

    // Test Get Stats
    console.log('3. Testing get stats...');
    const stats = await usersApi.getStats();
    console.log('✓ Stats retrieved:', stats);

    // Test Get History
    console.log('4. Testing get history...');
    const history = await usersApi.getHistory();
    console.log('✓ History retrieved:', history.tasks.length, 'tasks');

    // Test Get Leaderboard
    console.log('5. Testing get leaderboard...');
    const leaderboard = await usersApi.getLeaderboard({ limit: 10 });
    console.log('✓ Leaderboard retrieved:', leaderboard.length, 'users');

    console.log('✓ All users tests passed!\n');
    return true;
  } catch (error) {
    console.error('✗ Users test failed:', error);
    return false;
  }
};

/**
 * Run All Tests
 */
export const runAllTests = async () => {
  console.log('='.repeat(50));
  console.log('Running API Integration Tests');
  console.log('='.repeat(50));
  console.log();

  const results = {
    auth: await testAuth(),
    tasks: await testTasks(),
    agents: await testAgents(),
    users: await testUsers(),
  };

  console.log('='.repeat(50));
  console.log('Test Results:');
  console.log('='.repeat(50));
  console.log('Authentication:', results.auth ? '✓ PASSED' : '✗ FAILED');
  console.log('Tasks:', results.tasks ? '✓ PASSED' : '✗ FAILED');
  console.log('Agents:', results.agents ? '✓ PASSED' : '✗ FAILED');
  console.log('Users:', results.users ? '✓ PASSED' : '✗ FAILED');
  console.log('='.repeat(50));

  const allPassed = Object.values(results).every((result) => result);
  console.log(
    allPassed
      ? '✓ All tests passed!'
      : '✗ Some tests failed. Please check the logs above.'
  );

  return allPassed;
};

/**
 * Usage:
 *
 * import { runAllTests } from './services/api/test';
 *
 * // Run all tests
 * runAllTests();
 *
 * // Or run individual tests
 * testAuth();
 * testTasks();
 * testAgents();
 * testUsers();
 */
