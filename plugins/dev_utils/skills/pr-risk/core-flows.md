# Core flows

The paths users take every working day. A change that could stop a user finishing one of these is **High**, however small or isolated the diff is. The classes are where to start checking reach in commcare-android; they are not the whole flow.

## CommCare

Login → Start → Menu → Case selection → Form entry → Form submission → Sync

| Step | Start from |
|---|---|
| Login | `LoginActivity`, `CommCareSessionService` |
| Start (the Start button on the home screen) | `StandardHomeActivity` |
| Menu | `MenuActivity` |
| Case selection | `EntitySelectActivity`, `EntityDetailActivity` |
| Form entry | `FormEntryActivity` |
| Form submission | `FormRecordProcessor`, `ProcessAndSendTask` |
| Sync | `DataPullTask` |

## Connect

**PersonalID signup**: phone, verification, backup code, biometrics, through to a working account.

| Start from |
|---|
| `PersonalIdActivity`, `PersonalIdPhoneFragment`, `PersonalIdBackupCodeFragment`, `PersonalIdBiometricConfigFragment` |

**Opportunity**: find and claim → learn → deliver → payment.

| Step | Start from |
|---|---|
| Find and claim | `ConnectActivity`, `ConnectOpportunityListFragment`, `ConnectJobIntroFragment` |
| Learn | `ConnectLearningProgressFragment` |
| Deliver | `ConnectOpportunityHomeFragment`, `ConnectDeliveryHomeFragment`, `ConnectDeliveryVisitsFragment` |
| Payment | `ConnectDeliveryPaymentFragment` |

## Adding a flow

Add a flow here when a defect in it would stop most users of a product doing their job. Name the steps in the order a user takes them and give each step a class to start from.
