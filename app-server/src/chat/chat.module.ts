import { Module } from '@nestjs/common';
import { ChatService } from './chat.service';
import { ChatController } from './chat.controller';
import { HttpModule } from '@nestjs/axios';
import { RagModule } from 'src/rag/rag.module';

@Module({
  imports: [HttpModule, RagModule],
  controllers: [ChatController],
  providers: [ChatService],
})
export class ChatModule {}
