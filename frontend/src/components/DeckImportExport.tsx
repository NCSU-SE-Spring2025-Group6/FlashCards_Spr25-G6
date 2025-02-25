import React from 'react';
import http from '../utils/api';
import Swal from 'sweetalert2';

interface DeckImportExportProps {
  deckId?: string;
  onImportSuccess?: () => void;
  mode: 'import' | 'export'; // Add mode prop to determine which button to show
}

const DeckImportExport: React.FC<DeckImportExportProps> = ({ deckId, onImportSuccess, mode }) => {
  const handleExport = async () => {
    try {
      const response = await http.get(`/deck/${deckId}/export`);
      const { data, filename } = response.data;
      
      // Create and download the file
      const blob = new Blob([atob(data)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      Swal.fire({
        icon: 'success',
        title: 'Export Successful!',
        text: 'Your deck has been exported successfully'
      });
    } catch (error) {
      console.error('Export failed:', error);
      Swal.fire({
        icon: 'error',
        title: 'Export Failed',
        text: 'Failed to export deck'
      });
    }
  };

  const handleImport = async () => {
    try {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = '.json';
      
      input.onchange = async (e: Event) => {
        const target = e.target as HTMLInputElement;
        const file = target.files?.[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = async (event: ProgressEvent<FileReader>) => {
          try {
            const result = event.target?.result;
            if (typeof result !== 'string') return;
            
            const base64Content = btoa(result);
            const flashCardUser = window.localStorage.getItem('flashCardUser');
            const userData = flashCardUser ? JSON.parse(flashCardUser) : { localId: '' };
            
            if (!userData.localId) {
              throw new Error('User not authenticated');
            }
            
            const response = await http.post('/deck/import', {
              fileContent: base64Content,
              userId: userData.localId
            });

            if (response.data.deckId) {
              Swal.fire({
                icon: 'success',
                title: 'Import Successful!',
                text: 'Your deck has been imported successfully'
              });
              if (onImportSuccess) {
                onImportSuccess();
              }
            }
          } catch (error) {
            console.error('Import failed:', error);
            Swal.fire({
              icon: 'error',
              title: 'Import Failed',
              text: 'Failed to import deck'
            });
          }
        };
        reader.readAsText(file);
      };

      input.click();
    } catch (error) {
      console.error('Import failed:', error);
      Swal.fire({
        icon: 'error',
        title: 'Import Failed',
        text: 'Failed to import deck'
      });
    }
  };

  return (
    <div className="deck-import-export">
      {mode === 'export' && (
        <button
          className="btn btn-outline-primary"
          onClick={handleExport}
        >
          <i className="lni lni-download"></i> Export
        </button>
      )}
      {mode === 'import' && (
        <button
          className="btn btn-outline-primary"
          onClick={handleImport}
        >
          <i className="lni lni-upload"></i> Import
        </button>
      )}
    </div>
  );
};

export default DeckImportExport; 