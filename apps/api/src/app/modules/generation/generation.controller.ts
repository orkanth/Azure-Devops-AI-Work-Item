
import { Body, Controller, Post } from '@nestjs/common';

import { GenerateBoardDto } from './dto/generate-board.dto';
import { GenerationService } from './generation.service';

@Controller('generation')
export class GenerationController {
  constructor(
    private readonly generationService: GenerationService,
  ) {}

  @Post('board')
  generateBoard(@Body() dto: GenerateBoardDto): ReturnType<GenerationService['generateBoard']> {
    return this.generationService.generateBoard(dto);
  }
}
