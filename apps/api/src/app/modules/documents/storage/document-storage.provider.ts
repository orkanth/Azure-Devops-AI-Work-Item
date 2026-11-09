
export interface StoredDocument {
  storageProvider: 'local' | 'azure-blob';
  storageKey: string;
  fileName: string;
  contentType: string;
  sizeBytes: number;
}

export interface DocumentStorageProvider {
  save(
    documentId: string,
    file: Express.Multer.File,
  ): Promise<StoredDocument>;

  delete(storageKey: string): Promise<void>;
}

export const DOCUMENT_STORAGE_PROVIDER =
  Symbol('DOCUMENT_STORAGE_PROVIDER');
