
import 'dotenv/config';

import { DataSource } from 'typeorm'; 
import { DocumentEntity } from '../app/modules/documents/entities/document.entity';
import { DocumentIngestionJobEntity } from '../app/modules/documents/entities/document-ingestion-job.entity';

export const AppDataSource = new DataSource({
  type: 'postgres',
  host: process.env.DB_HOST || 'localhost',
  port: Number(process.env.DB_PORT || 5432),
  username: process.env.DB_USERNAME,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_DATABASE,

  entities: [DocumentEntity, DocumentIngestionJobEntity],

  migrations: [
    __dirname + '/migrations/*{.ts,.js}',
  ],

  synchronize: false,
  migrationsRun: false,
});
