import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { AppFeedbackService } from '../services/app-feedback.service';

/** Provides a consistent, user-safe message for failed API requests. */
export const apiErrorInterceptor: HttpInterceptorFn = (request, next) => {
  const feedback = inject(AppFeedbackService);

  return next(request).pipe(
    catchError((error: unknown) => {
      if (error instanceof HttpErrorResponse) {
        const message =
          error.status === 0
            ? 'The API service could not be reached. Check that the backend is running.'
            : error.status >= 500
              ? 'The service encountered an unexpected error. Please try again.'
              : 'The request could not be completed. Check the details and try again.';

        feedback.show(message, 'error');
      }

      return throwError(() => error);
    }),
  );
};
