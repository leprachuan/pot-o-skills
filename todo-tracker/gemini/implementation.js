/**
 * Gemini implementation of TODO Tracker skill.
 * Handles TODO management requests for Gemini runtime.
 */

const TodoManager = require('../todo_manager.js');

async function processTodoRequest(request) {
  /**
   * Process natural language TODO requests.
   *
   * Examples:
   * - "Add buy milk to my todos"
   * - "What are my upcoming todos?"
   * - "Mark review PR as complete"
   * - "Show me overdue tasks"
   */
  const manager = new TodoManager();
  const requestLower = request.toLowerCase();

  // Detect request type and respond
  if (['add', 'create', 'new'].some(word => requestLower.includes(word))) {
    return await handleAddRequest(manager, request);
  } else if (['complete', 'done', 'finish', 'mark'].some(word => requestLower.includes(word))) {
    return await handleCompleteRequest(manager, request);
  } else if (['upcoming', 'due soon', 'next'].some(word => requestLower.includes(word))) {
    return await handleUpcomingRequest(manager);
  } else if (['overdue', 'past due', 'late'].some(word => requestLower.includes(word))) {
    return await handleOverdueRequest(manager);
  } else if (['list', 'show', 'what'].some(word => requestLower.includes(word))) {
    return await handleListRequest(manager);
  } else {
    return "I can help you manage TODOs. Try: 'Add...', 'Show upcoming', 'Mark complete', etc.";
  }
}

async function handleAddRequest(manager, request) {
  /**Handle add TODO requests.*/
  const todos = await manager.loadTodos();
  todos.push({
    description: request,
    completed: false,
    section: 'Active',
    due: null,
    labels: [],
    notes: '',
  });
  await manager.saveTodos(todos);
  return "✓ Added TODO";
}

async function handleCompleteRequest(manager, request) {
  /**Handle complete TODO requests.*/
  const todos = await manager.loadTodos();
  if (todos.length > 0) {
    const firstTodo = todos[0];
    firstTodo.completed = true;
    firstTodo.section = 'Completed';
    await manager.saveTodos(todos);
    return `✓ Completed: ${firstTodo.description}`;
  }
  return "No TODOs to complete";
}

async function handleUpcomingRequest(manager) {
  /**Handle upcoming TODOs request.*/
  const todos = await manager.getUpcoming();
  if (todos.length === 0) {
    return "No upcoming TODOs";
  }

  let response = "Upcoming TODOs:\n";
  for (const todo of todos) {
    response += `• ${todo.description} (due ${todo.due})\n`;
  }
  return response;
}

async function handleOverdueRequest(manager) {
  /**Handle overdue TODOs request.*/
  const todos = await manager.getOverdue();
  if (todos.length === 0) {
    return "No overdue TODOs";
  }

  let response = "Overdue TODOs:\n";
  for (const todo of todos) {
    response += `• ${todo.description} (due ${todo.due})\n`;
  }
  return response;
}

async function handleListRequest(manager) {
  /**Handle list TODOs request.*/
  const todos = await manager.loadTodos();
  if (todos.length === 0) {
    return "No TODOs";
  }

  const active = todos.filter(t => !t.completed);
  const completed = todos.filter(t => t.completed);

  let response = "";
  if (active.length > 0) {
    response += "Active TODOs:\n";
    for (const todo of active) {
      response += `○ ${todo.description}`;
      if (todo.due) {
        response += ` (due ${todo.due})`;
      }
      response += "\n";
    }
  }

  if (completed.length > 0) {
    response += "\nCompleted TODOs:\n";
    for (const todo of completed) {
      response += `✓ ${todo.description}\n`;
    }
  }

  return response;
}

module.exports = {
  processTodoRequest,
};
