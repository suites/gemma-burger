import { Module } from '@nestjs/common';
import { join } from 'path';
import { ServeStaticModule } from '@nestjs/serve-static';
import { ChatModule } from './chat/chat.module';
import { RagModule } from './rag/rag.module';

@Module({
  imports: [
    ServeStaticModule.forRoot({
      rootPath: join(__dirname, '..', 'public'), // public 폴더를 루트로 지정
    }),
    ChatModule,
    RagModule,
  ],
  controllers: [],
  providers: [],
})
export class AppModule {}
