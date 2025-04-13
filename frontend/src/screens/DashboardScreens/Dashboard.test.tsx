import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Dashboard from './Dashboard';
import http from 'utils/api'; // Ensure the path is correct for your project
import { MemoryRouter } from 'react-router-dom';
import Swal, { SweetAlertResult } from 'sweetalert2'; // Ensure to import SweetAlertResult
import { act } from "react-dom/test-utils"; // To use act for state updates

// Mock the Axios library
jest.mock('utils/api'); // Adjust path as needed


describe('Dashboard Component', () => {
    const mockFetchDecksResponse = {
      data: {
        decks: [
          {
            id: '1',
            userId: '1',
            title: 'Deck 1',
            description: 'Description for Deck 1',
            visibility: 'public',
            cards_count: 5,
            lastOpened: new Date().toISOString(),
          },
        ],
      },
    };
  
    const mockFetchFoldersResponse = {
      data: {
        folders: [
          {
            id: 'folder1',
            name: 'Folder 1',
            decks: [],
          },
        ],
      },
    };
  
    beforeEach(() => {
      jest.clearAllMocks();
  
      // Mock the API calls
      (http.get as jest.Mock).mockImplementation((url) => {
        if (url === '/deck/all') {
          return Promise.resolve(mockFetchDecksResponse);
        }
        if (url === '/folders/all') {
          return Promise.resolve(mockFetchFoldersResponse);
        }
        if (url === '/decks/folder1') { // Mock response for folder decks
          return Promise.resolve({ data: { decks: [] } }); // No decks in this folder
        }
        return Promise.reject(new Error('Not found'));
      });
  
      // Mock the Swal.fire function
      jest.spyOn(Swal, 'fire').mockImplementation(() => {
        return Promise.resolve({
          isConfirmed: true,
          isDenied: false,
          isDismissed: false,
        } as SweetAlertResult);
      });
    });

  test('renders the Dashboard component and fetches decks and folders', async () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    // Wait for the decks and folders to be fetched
    await waitFor(async () => {
      const decks = await screen.findAllByText('Deck 1');
      expect(decks.length).toBe(2); // Adjust the expected count based on your data
      // Use getByRole to specify we're looking for the heading
      expect(screen.getByRole('heading', { name: /Folder 1/i })).toBeInTheDocument();
    });
  });

  test('displays empty state when no folders are available', async () => {
    (http.get as jest.Mock).mockImplementationOnce((url) => {
      if (url === '/folders/all') {
        return Promise.resolve({ data: { folders: [] } });
      }
      return Promise.reject(new Error('Not found'));
    });

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('No folders created yet.')).toBeInTheDocument();
    });
  });

  
  test('opens folder modal when folder is clicked', async () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    // Wait for the folder list to load
    await waitFor(() => {
      // Use getByRole to find the specific heading
      expect(screen.getByRole('heading', { name: 'Folder 1' })).toBeInTheDocument();
    });

    // Click the folder to open the modal
    fireEvent.click(screen.getByRole('heading', { name: 'Folder 1' }));

    // Wait for the modal to be displayed
    await waitFor(() => {
      expect(screen.getByText('Folder Decks')).toBeInTheDocument();
    });

    // Check if no decks are present in the folder
    expect(screen.getByText('No decks in this folder.')).toBeInTheDocument();
  });

  test('deletes a deck and shows success alert', async () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    // Wait for the folder list to load
    await waitFor(() => {
        // Use getByRole to find the specific heading
        expect(screen.getByRole('heading', { name: 'Folder 1' })).toBeInTheDocument();
    });
  
    // Click on the delete button
    const deleteButton = screen.getByRole('button', { name: /Delete/i });
    fireEvent.click(deleteButton);

    // Confirm deletion
    fireEvent.click(screen.getByText('Yes'));

    // Wait for the success alert to be shown
    await waitFor(() => {
      expect(Swal.fire).toHaveBeenCalledWith(
        'Deck Deleted Successfully!',
        '',
        'success'
      );
    });
  });

  test('deletes a deck and shows confirmation popup', async () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
        // Use getByRole to find the specific heading
        expect(screen.getByRole('heading', { name: 'Folder 1' })).toBeInTheDocument();
    });

    // Click the delete button to open the confirmation popup
    const deleteButton = screen.getByRole('button', { name: /Delete/i });
    fireEvent.click(deleteButton);

    // Check for the confirmation message in the popup
    const confirmationMessage = screen.getByText(/Are you sure to delete this deck?/i);
    expect(confirmationMessage).toBeInTheDocument();

    // Check if the Yes and No buttons are present
    const yesButton = screen.getByRole('button', { name: /Yes/i });
    const noButton = screen.getByRole('button', { name: /No/i });

    expect(yesButton).toBeInTheDocument();
    expect(noButton).toBeInTheDocument();

    // If you want to simulate clicking "Yes" to confirm deletion:
    fireEvent.click(yesButton);

    // Check for the success alert after deletion confirmation
    await waitFor(() => {
      expect(Swal.fire).toHaveBeenCalledWith(
        'Deck Deleted Successfully!',
        '',
        'success'
      );
    });
  });
});
