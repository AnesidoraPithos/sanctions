# Test Document

## 1. Test Overview

Describe the testing approach used to validate the system.

**Objective**

Verify that the implemented solution satisfies the **MVP requirements**, meets the **acceptance criteria**, and supports the defined **user journeys**.

**Test Types**

- Unit Tests
- API / Service Tests
- Integration Tests
- UI / End-to-End Tests (if applicable)

**Tools Used**

Example:

- pytest
- Jest
- Postman
- coverage.py

---

# 2. Test Environment

Describe the environment where tests were executed.

| Component | Description |
|----------|-------------|
| Backend | e.g. Python FastAPI |
| Frontend | e.g. React |
| Database | e.g. PostgreSQL |
| Runtime | e.g. Docker |
| OS | e.g. MacOS / Linux |

---

# 3. Test Cases

## Test Case Summary

| Test ID | Requirement ID | Description | Test Type | Expected Result |
|--------|----------------|-------------|-----------|----------------|
| TC-01 | US-01 | Create a task | API | Task created successfully |
| TC-02 | US-02 | View task list | UI | Task list displayed |

---

## Test Case Details

### TC-01 – Create Task

**Requirement:** US-01  
**Test Type:** API Test  

**Description**

Verify that a user can create a new task.

**Steps**

1. Send POST request to `/tasks`
2. Provide task title and description

**Expected Result**

- API returns success response
- Task is stored in database
- Task appears in task list

---

### TC-02 – View Tasks

**Requirement:** US-02  
**Test Type:** UI Test  

**Description**

Verify that users can view their tasks.

**Steps**

1. Navigate to the task page
2. Load the task list

**Expected Result**

- Task list is displayed
- Tasks appear correctly

---

# 4. Test Execution Results

| Test ID | Status | Notes |
|-------|--------|------|
| TC-01 | Pass | API returned success |
| TC-02 | Pass | Tasks displayed correctly |

Status values:

- Pass
- Fail
- Blocked

---

# 5. Requirements Traceability Matrix

This matrix ensures that all **MVP requirements are verified by tests**.

| Requirement ID | User Story | Acceptance Criteria | Test Case(s) | Status |
|----------------|-----------|--------------------|--------------|--------|
| US-01 | Create Task | User can create a task | TC-01 | Pass |
| US-02 | View Tasks | User can view task list | TC-02 | Pass |

---

# 6. Test Coverage

Summarize the coverage of the testing effort.

**Functional Coverage**

| Feature | Tested | Test Case |
|-------|-------|----------|
| Create Task | Yes | TC-01 |
| View Tasks | Yes | TC-02 |

**Code Coverage**

Example:

- Unit test coverage: 75%
- Core service modules covered
- Utility modules partially covered

Tools used:

- coverage.py
- jest coverage

---

# 7. Defects / Observations

Document any issues discovered during testing.

| Issue ID | Description | Status |
|---------|-------------|-------|
| BUG-01 | API fails when title is empty | Fixed |
| BUG-02 | UI layout issue on mobile | Pending |

---

# 8. Key Findings

Summarize key insights from testing.

Example:

- Input validation was added for empty task titles
- Error handling improved for API failures
- System successfully supports all MVP user journeys

---

# 9. Conclusion

Summarize the testing outcome.

Example:

All MVP requirements were verified through unit and integration tests.  
The system successfully supports the defined user journeys and is ready for demonstration.