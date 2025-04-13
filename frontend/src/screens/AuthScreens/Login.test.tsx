import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Login from "./Login";
import http from "utils/api";
import { MemoryRouter } from "react-router-dom";
import Swal from "sweetalert2"; // Import Swal for testing

// Mock dependencies
jest.mock("utils/api");
jest.mock("sweetalert2", () => ({
  fire: jest.fn(),
}));

// Mock the localStorage methods
beforeAll(() => {
  Object.defineProperty(window, 'localStorage', {
    value: {
      setItem: jest.fn(),
      getItem: jest.fn(() => null),
      removeItem: jest.fn(),
      clear: jest.fn(),
    },
    writable: true,
  });
});

describe("Login Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders login form with email, password, and login button", () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>
    );

    expect(screen.getByLabelText(/Email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Login/i })).toBeInTheDocument();
  });

  test("displays 'Logging in...' when isSubmitting is true", async () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>
    );

    const emailInput = screen.getByLabelText(/Email address/i);
    const passwordInput = screen.getByLabelText(/Password/i);
    const loginButton = screen.getByRole("button", { name: /Login/i });

    userEvent.type(emailInput, "test@example.com");
    userEvent.type(passwordInput, "password123");

    // Mock successful API response
    (http.post as jest.Mock).mockResolvedValue({
      data: { user: { name: "Test User" } },
    });

    userEvent.click(loginButton);

    // Assert "Logging in..." is displayed
    expect(loginButton).toHaveTextContent("Logging in...");
    await waitFor(() => expect(loginButton).toHaveTextContent("Login"));
  });

  test("handles successful login", async () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>
    );

    const emailInput = screen.getByLabelText(/Email address/i);
    const passwordInput = screen.getByLabelText(/Password/i);
    const loginButton = screen.getByRole("button", { name: /Login/i });

    userEvent.type(emailInput, "test@example.com");
    userEvent.type(passwordInput, "password123");

    (http.post as jest.Mock).mockResolvedValue({
      data: { user: { name: "Test User" } },
    });

    userEvent.click(loginButton);

    // Wait for SweetAlert to be called
    await waitFor(() => {
      expect(window.localStorage.setItem).toHaveBeenCalledWith(
        "flashCardUser",
        JSON.stringify({ name: "Test User" })
      );
      expect(Swal.fire).toHaveBeenCalledWith(
        expect.objectContaining({
          icon: 'success',
          title: 'Login Successful!',
          text: 'You have successfully logged in',
        })
      );
    });
  });

  test("handles login failure", async () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>
    );

    const emailInput = screen.getByLabelText(/Email address/i);
    const passwordInput = screen.getByLabelText(/Password/i);
    const loginButton = screen.getByRole("button", { name: /Login/i });

    userEvent.type(emailInput, "wrong@example.com");
    userEvent.type(passwordInput, "wrongpassword");

    // Mock failed API response
    (http.post as jest.Mock).mockRejectedValue(new Error("Login Failed"));

    userEvent.click(loginButton);

    // Wait for SweetAlert to be called
    await waitFor(() => {
      expect(Swal.fire).toHaveBeenCalledWith(
        expect.objectContaining({
          icon: 'error',
          title: 'Login Failed!',
          text: 'An error occurred, please try again',
        })
      );
    });
  });
});
