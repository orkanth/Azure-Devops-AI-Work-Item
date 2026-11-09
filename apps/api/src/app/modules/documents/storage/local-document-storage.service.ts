
import {
  BadRequestException,
  Injectable,
} from '@nestjs/common';
import { promises as fs } from 'node:fs';
import path from 'node:path';

import {
  DocumentStorageProvider,
  StoredDocument,
} from './document-storage.provider';

@Injectable()
export class LocalDocumentStorageService
  implements DocumentStorageProvider
{
  private readonly storageRoot = path.resolve(
    process.cwd(),
    process.env.DOCUMENT_STORAGE_PATH || 'local-data',
  );

  async save(
    documentId: string,
    file: Express.Multer.File,
  ): Promise<StoredDocument> {
    if (!/^[a-zA-Z0-9_-]+$/.test(documentId)) {
      throw new BadRequestException('Invalid document ID.');
    }

    if (!file?.buffer) {
      throw new BadRequestException('File content is missing.');
    }

    const originalName = path.basename(
      file.originalname.replace(/\\/g, '/'),
    );

    const safeFileName = originalName
      .replace(/[^a-zA-Z0-9._-]/g, '_')
      .slice(0, 180);

    if (!safeFileName || safeFileName === '.' || safeFileName === '..') {
      throw new BadRequestException('Invalid file name.');
    }

    const storageKey = `documents/${documentId}/${safeFileName}`;

    const destination = path.resolve(
      this.storageRoot,
      ...storageKey.split('/'),
    );

    if (!destination.startsWith(`${this.storageRoot}${path.sep}`)) {
      throw new BadRequestException('Invalid storage path.');
    }

    await fs.mkdir(path.dirname(destination), {
      recursive: true,
    });

    await fs.writeFile(destination, file.buffer, {
      flag: 'wx',
    });

    return {
      storageProvider: 'local',
      storageKey,
      fileName: safeFileName,
      contentType: file.mimetype,
      sizeBytes: file.size,
    };
  }

  async delete(storageKey: string): Promise<void> {
    if (
      !storageKey.startsWith('documents/') ||
      storageKey.includes('\\')
    ) {
      throw new BadRequestException('Invalid storage key.');
    }

    const destination = path.resolve(
      this.storageRoot,
      ...storageKey.split('/'),
    );

    if (!destination.startsWith(`${this.storageRoot}${path.sep}`)) {
      throw new BadRequestException('Invalid storage path.');
    }

    try {
      await fs.unlink(destination);

      await fs.rm(path.dirname(destination), {
        recursive: true,
        force: true,
      });
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== 'ENOENT') {
        throw error;
      }
    }
  }
}
